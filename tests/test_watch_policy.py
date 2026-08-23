"""Tests for the watch policy that guards live reload.

Covers the safety checks that decide between recursively watching the main
file's directory and safe mode (main file + explicit paths + served files),
the JSON watch manifest, Drafter-specific ignore rules, the new watch
configuration settings, the dynamic WatchSet, and the use_reloader lifecycle
fix (no watcher task at all when the reloader is disabled).
"""

import argparse
import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from drafter.app import app_server
from drafter.app.error_log import DEBUG_LOG_FILENAME
from drafter.app.watch_policy import (
    IgnoreRules,
    build_watch_plan,
    describe_unsafe_directory,
    is_broad_location,
    load_watch_manifest,
    resolve_watch_entries,
    safe_mode_notice,
    scan_exceeds_limits,
)
from drafter.app.watcher import WatchedPath, WatchSet
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_common import AppCommonConfiguration
from drafter.config.app_server import AppServerConfiguration
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.system import SystemConfiguration
from drafter.configuration import (
    _reset_system_for_testing,
    _set_system_for_testing,
)

FAKE_SOURCE = "from drafter import *\nstart_server()\n"


def make_system(path: str | None, **app_server_kwargs) -> SystemConfiguration:
    app_common = AppCommonConfiguration()
    app_common.prerender_initial_page = False
    system = SystemConfiguration(
        bootstrap=BootstrapConfiguration(path=path),
        client_server=ClientServerConfiguration(),
        app_server=AppServerConfiguration(),
        app_builder=AppBuilderConfiguration(),
        app_common=app_common,
    )
    system.app_server.open_browser = False
    for key, value in app_server_kwargs.items():
        setattr(system.app_server, key, value)
    return system


def make_project(tmp_path: Path) -> Path:
    main = tmp_path / "main.py"
    main.write_text(FAKE_SOURCE, encoding="utf-8")
    return main


def plan_for(system, main: Path, home: Path | None = None, on_disk: bool = True):
    return build_watch_plan(
        system, main.parent, main, main_file_on_disk=on_disk, home=home
    )


# ---------------------------------------------------------------------------
# Configuration settings
# ---------------------------------------------------------------------------


class TestConfiguration:
    def test_defaults(self):
        config = AppServerConfiguration()
        assert config.use_reloader is True
        assert config.watch_adjacent_files is True
        assert config.watch_recursively is True
        assert config.watch_safe_mode is True
        assert config.watch_served_files is True
        assert config.watch_max_files == 1000
        assert config.watch_max_directories == 200
        assert config.watch_max_depth == 20
        assert config.watch_broad_locations is False
        assert config.watch_paths == []
        assert config.ignore_watch_paths == []
        assert config.watch_manifest is None
        assert config.watch_force_recursive is False

    def test_list_defaults_are_not_shared(self):
        first, second = AppServerConfiguration(), AppServerConfiguration()
        first.watch_paths.append("a.py")
        assert second.watch_paths == []

    def test_env_vars(self):
        parsed = AppServerConfiguration.parse_env_variables(
            {
                "DRAFTER_WATCH_ADJACENT_FILES": "false",
                "DRAFTER_WATCH_RECURSIVELY": "0",
                "DRAFTER_WATCH_SAFE_MODE": "no",
                "DRAFTER_WATCH_SERVED_FILES": "true",
                "DRAFTER_WATCH_MAX_FILES": "5",
                "DRAFTER_WATCH_MAX_DIRECTORIES": "6",
                "DRAFTER_WATCH_MAX_DEPTH": "7",
                "DRAFTER_WATCH_BROAD_LOCATIONS": "1",
                "DRAFTER_WATCH_PATHS": "a.py;data/",
                "DRAFTER_IGNORE_WATCH_PATHS": "*.log",
                "DRAFTER_WATCH_MANIFEST": "manifest.json",
                "DRAFTER_WATCH_FORCE_RECURSIVE": "yes",
            }
        )
        assert parsed["watch_adjacent_files"] is False
        assert parsed["watch_recursively"] is False
        assert parsed["watch_safe_mode"] is False
        assert parsed["watch_served_files"] is True
        assert parsed["watch_max_files"] == 5
        assert parsed["watch_max_directories"] == 6
        assert parsed["watch_max_depth"] == 7
        assert parsed["watch_broad_locations"] is True
        assert parsed["watch_paths"] == ["a.py", "data/"]
        assert parsed["ignore_watch_paths"] == ["*.log"]
        assert parsed["watch_manifest"] == "manifest.json"
        assert parsed["watch_force_recursive"] is True

    def make_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        AppServerConfiguration.extend_parser(parser)
        return parser

    def test_cli_flags(self):
        parsed, _ = self.make_parser().parse_known_args(
            [
                "--no-watch-adjacent-files",
                "--no-watch-recursively",
                "--no-watch-safe-mode",
                "--no-watch-served-files",
                "--watch-max-files=9",
                "--watch-broad-locations",
                "--watch-path=helpers.py",
                "--watch-path=images/",
                "--ignore-watch-path=*.log",
                "--watch-manifest=manifest.json",
                "--watch-force-recursive",
            ]
        )
        result = AppServerConfiguration.parse_args(vars(parsed))
        assert result["watch_adjacent_files"] is False
        assert result["watch_recursively"] is False
        assert result["watch_safe_mode"] is False
        assert result["watch_served_files"] is False
        assert result["watch_max_files"] == 9
        assert result["watch_broad_locations"] is True
        assert result["watch_paths"] == ["helpers.py", "images/"]
        assert result["ignore_watch_paths"] == ["*.log"]
        assert result["watch_manifest"] == "manifest.json"
        assert result["watch_force_recursive"] is True

    def test_cli_flags_absent_report_nothing(self):
        # Otherwise argparse defaults would clobber env vars during merging.
        parsed, _ = self.make_parser().parse_known_args([])
        result = AppServerConfiguration.parse_args(vars(parsed))
        assert not any(key.startswith(("watch_", "ignore_watch")) for key in result)


# ---------------------------------------------------------------------------
# Ignore rules
# ---------------------------------------------------------------------------


class TestIgnoreRules:
    def test_generated_files_always_ignored(self, tmp_path):
        rules = IgnoreRules(base_directory=tmp_path)
        assert rules.should_ignore(tmp_path / DEBUG_LOG_FILENAME)

    def test_name_glob(self, tmp_path):
        rules = IgnoreRules(base_directory=tmp_path, patterns=("*.log",))
        assert rules.should_ignore(tmp_path / "server.log")
        assert not rules.should_ignore(tmp_path / "main.py")

    def test_directory_pattern(self, tmp_path):
        rules = IgnoreRules(base_directory=tmp_path, patterns=("output/",))
        assert rules.should_ignore(tmp_path / "output" / "result.txt")
        assert rules.should_ignore(tmp_path / "output")
        assert not rules.should_ignore(tmp_path / "outputs" / "x.txt")

    def test_relative_glob(self, tmp_path):
        rules = IgnoreRules(base_directory=tmp_path, patterns=("data/*.tmp",))
        assert rules.should_ignore(tmp_path / "data" / "scratch.tmp")
        assert not rules.should_ignore(tmp_path / "data" / "pets.csv")


# ---------------------------------------------------------------------------
# Safety checks
# ---------------------------------------------------------------------------


class TestSafetyChecks:
    def config(self, **kwargs):
        return AppServerConfiguration(**kwargs)

    def test_filesystem_root_is_unsafe(self, tmp_path):
        root = Path(tmp_path.anchor)
        reason = describe_unsafe_directory(root, self.config(), home=tmp_path)
        assert reason == "it is a filesystem root"

    def test_home_directory_is_unsafe(self, tmp_path):
        reason = describe_unsafe_directory(tmp_path, self.config(), home=tmp_path)
        assert reason == "it is your home directory"

    @pytest.mark.parametrize("name", ["Desktop", "Documents", "Downloads"])
    def test_broad_locations_are_unsafe(self, tmp_path, name):
        broad = tmp_path / name
        broad.mkdir()
        reason = describe_unsafe_directory(broad, self.config(), home=tmp_path)
        assert reason is not None and name in reason

    def test_onedrive_nested_documents_is_broad(self, tmp_path):
        nested = tmp_path / "OneDrive" / "Documents"
        nested.mkdir(parents=True)
        assert is_broad_location(nested.resolve(), tmp_path.resolve())

    def test_broad_locations_allowed_when_configured(self, tmp_path):
        broad = tmp_path / "Desktop"
        broad.mkdir()
        config = self.config(watch_broad_locations=True)
        assert describe_unsafe_directory(broad, config, home=tmp_path) is None

    def test_ordinary_small_directory_is_safe(self, tmp_path):
        lab = tmp_path / "lab3"
        lab.mkdir()
        (lab / "main.py").write_text("x = 1", encoding="utf-8")
        assert describe_unsafe_directory(lab, self.config(), home=tmp_path) is None

    def test_too_many_files(self, tmp_path):
        for index in range(6):
            (tmp_path / f"file{index}.txt").write_text("x", encoding="utf-8")
        assert scan_exceeds_limits(tmp_path, 5, None, None) == (
            "it contains more than 5 files"
        )
        assert scan_exceeds_limits(tmp_path, 6, None, None) is None

    def test_too_many_directories(self, tmp_path):
        for index in range(4):
            (tmp_path / f"folder{index}").mkdir()
        assert scan_exceeds_limits(tmp_path, None, 3, None) == (
            "it contains more than 3 folders"
        )
        assert scan_exceeds_limits(tmp_path, None, 4, None) is None

    def test_too_deep(self, tmp_path):
        deep = tmp_path / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)
        assert scan_exceeds_limits(tmp_path, None, None, 3) == (
            "it contains folders nested more than 3 levels deep"
        )
        assert scan_exceeds_limits(tmp_path, None, None, 4) is None

    def test_no_limits_means_no_scan(self, tmp_path):
        for index in range(10):
            (tmp_path / f"file{index}.txt").write_text("x", encoding="utf-8")
        assert scan_exceeds_limits(tmp_path, None, None, None) is None

    def test_git_internals_do_not_count(self, tmp_path):
        git_objects = tmp_path / ".git" / "objects"
        git_objects.mkdir(parents=True)
        for index in range(20):
            (git_objects / f"blob{index}").write_text("x", encoding="utf-8")
        assert scan_exceeds_limits(tmp_path, 5, 5, None) is None


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


class TestManifest:
    def write_manifest(self, tmp_path, data) -> Path:
        manifest = tmp_path / "manifest.json"
        manifest.write_text(json.dumps(data), encoding="utf-8")
        return manifest

    def test_list_form(self, tmp_path):
        manifest = self.write_manifest(tmp_path, ["helpers.py", "images/"])
        watch, ignore, error = load_watch_manifest(manifest)
        assert (watch, ignore, error) == (["helpers.py", "images/"], [], None)

    def test_dict_form(self, tmp_path):
        manifest = self.write_manifest(
            tmp_path,
            {"watch_paths": ["data/*.csv"], "ignore_watch_paths": ["*.log"]},
        )
        watch, ignore, error = load_watch_manifest(manifest)
        assert (watch, ignore, error) == (["data/*.csv"], ["*.log"], None)

    def test_missing_file(self, tmp_path):
        watch, ignore, error = load_watch_manifest(tmp_path / "nope.json")
        assert (watch, ignore) == ([], [])
        assert error is not None and "Could not read" in error

    def test_invalid_json(self, tmp_path):
        manifest = tmp_path / "manifest.json"
        manifest.write_text("{not json", encoding="utf-8")
        _, _, error = load_watch_manifest(manifest)
        assert error is not None

    def test_wrong_shape(self, tmp_path):
        manifest = self.write_manifest(tmp_path, "just a string")
        _, _, error = load_watch_manifest(manifest)
        assert error is not None and "list or object" in error


class TestResolveWatchEntries:
    def test_plain_and_absolute_paths(self, tmp_path):
        absolute = tmp_path / "elsewhere.py"
        resolved = resolve_watch_entries(["helpers.py", str(absolute)], tmp_path)
        assert resolved == [tmp_path / "helpers.py", absolute]

    def test_glob_expansion(self, tmp_path):
        data = tmp_path / "data"
        data.mkdir()
        (data / "a.csv").write_text("x", encoding="utf-8")
        (data / "b.csv").write_text("x", encoding="utf-8")
        (data / "c.txt").write_text("x", encoding="utf-8")
        resolved = resolve_watch_entries(["data/*.csv"], tmp_path)
        assert resolved == [data / "a.csv", data / "b.csv"]


# ---------------------------------------------------------------------------
# Watch plan
# ---------------------------------------------------------------------------


class TestBuildWatchPlan:
    def test_small_project_watched_recursively(self, tmp_path):
        home = tmp_path / "home"
        lab = home / "lab3"
        lab.mkdir(parents=True)
        main = make_project(lab)
        system = make_system(str(main))
        plan = plan_for(system, main, home=home)
        assert not plan.safe_mode
        assert plan.safe_mode_reason is None
        assert not plan.track_served_files
        watched = {wp.directory for wp in plan.paths}
        assert main.resolve() in watched
        assert lab.resolve() in watched

    def test_broad_folder_enters_safe_mode(self, tmp_path):
        downloads = tmp_path / "Downloads"
        downloads.mkdir()
        main = make_project(downloads)
        system = make_system(str(main))
        plan = plan_for(system, main, home=tmp_path)
        assert plan.safe_mode
        assert plan.safe_mode_reason is not None
        assert plan.track_served_files
        watched = {wp.directory for wp in plan.paths}
        assert main.resolve() in watched
        assert downloads.resolve() not in watched

    def test_limit_exceeded_enters_safe_mode(self, tmp_path):
        main = make_project(tmp_path)
        for index in range(5):
            (tmp_path / f"extra{index}.txt").write_text("x", encoding="utf-8")
        home = tmp_path / "home"
        home.mkdir()
        system = make_system(str(main), watch_max_files=3)
        plan = plan_for(system, main, home=home)
        assert plan.safe_mode
        assert "more than 3 files" in plan.safe_mode_reason

    def test_watch_recursively_false_is_quiet_safe_mode(self, tmp_path):
        main = make_project(tmp_path)
        system = make_system(str(main), watch_recursively=False)
        plan = plan_for(system, main, home=tmp_path / "home")
        assert plan.safe_mode
        assert plan.safe_mode_reason is None  # configured, not "noticed"
        assert plan.track_served_files

    def test_watch_adjacent_files_false_is_main_file_only(self, tmp_path):
        main = make_project(tmp_path)
        system = make_system(str(main), watch_adjacent_files=False)
        plan = plan_for(system, main, home=tmp_path)  # even in home!
        assert not plan.safe_mode
        assert not plan.track_served_files
        assert [wp.directory for wp in plan.paths] == [main.resolve()]

    def test_force_recursive_overrides_safety(self, tmp_path):
        main = make_project(tmp_path)
        system = make_system(str(main), watch_force_recursive=True)
        plan = plan_for(system, main, home=tmp_path)  # home dir: normally refused
        assert not plan.safe_mode
        assert tmp_path.resolve() in {wp.directory for wp in plan.paths}

    def test_safe_mode_disabled_skips_checks(self, tmp_path):
        main = make_project(tmp_path)
        system = make_system(str(main), watch_safe_mode=False)
        plan = plan_for(system, main, home=tmp_path)
        assert not plan.safe_mode
        assert tmp_path.resolve() in {wp.directory for wp in plan.paths}

    def test_watch_served_files_false_disables_tracking(self, tmp_path):
        main = make_project(tmp_path)
        system = make_system(
            str(main), watch_recursively=False, watch_served_files=False
        )
        plan = plan_for(system, main, home=tmp_path / "home")
        assert plan.safe_mode
        assert not plan.track_served_files

    def test_explicit_watch_paths_apply_in_safe_mode(self, tmp_path):
        main = make_project(tmp_path)
        helpers = tmp_path / "helpers.py"
        helpers.write_text("x = 1", encoding="utf-8")
        images = tmp_path / "images"
        images.mkdir()
        system = make_system(
            str(main),
            watch_recursively=False,
            watch_paths=["helpers.py", "images/"],
        )
        plan = plan_for(system, main, home=tmp_path / "home")
        watched = {wp.directory for wp in plan.paths}
        assert helpers.resolve() in watched
        assert images.resolve() in watched

    def test_nonexistent_explicit_paths_are_skipped(self, tmp_path):
        main = make_project(tmp_path)
        system = make_system(str(main), watch_paths=["missing.py"])
        plan = plan_for(system, main, home=tmp_path / "home")
        assert (tmp_path / "missing.py").resolve() not in {
            wp.directory for wp in plan.paths
        }

    def test_manifest_entries_and_ignores(self, tmp_path):
        main = make_project(tmp_path)
        data = tmp_path / "data"
        data.mkdir()
        (data / "pets.csv").write_text("x", encoding="utf-8")
        manifest = tmp_path / "drafter-files.json"
        manifest.write_text(
            json.dumps(
                {"watch_paths": ["data/*.csv"], "ignore_watch_paths": ["*.log"]}
            ),
            encoding="utf-8",
        )
        system = make_system(
            str(main), watch_recursively=False, watch_manifest="drafter-files.json"
        )
        plan = plan_for(system, main, home=tmp_path / "home")
        assert (data / "pets.csv").resolve() in {wp.directory for wp in plan.paths}
        assert plan.ignore_rules.should_ignore(tmp_path / "server.log")
        assert not plan.warnings

    def test_unreadable_manifest_becomes_warning(self, tmp_path):
        main = make_project(tmp_path)
        system = make_system(str(main), watch_manifest="missing-manifest.json")
        plan = plan_for(system, main, home=tmp_path / "home")
        assert plan.warnings and "missing-manifest.json" in plan.warnings[0]

    def test_paths_are_deduplicated(self, tmp_path):
        main = make_project(tmp_path)
        system = make_system(str(main), watch_paths=["main.py", "main.py"])
        plan = plan_for(system, main, home=tmp_path / "home")
        main_entries = [wp for wp in plan.paths if wp.directory == main.resolve()]
        assert len(main_entries) == 1
        # The main file keeps its restart (not full reload) behavior.
        assert main_entries[0].full_reload is False

    def test_in_memory_source_only_full_reloads(self, tmp_path):
        main = tmp_path / "unsaved.py"  # never written to disk
        system = make_system(str(main))
        plan = plan_for(system, main, home=tmp_path / "home", on_disk=False)
        assert all(wp.full_reload for wp in plan.paths)
        assert main not in {wp.directory for wp in plan.paths}

    def test_safe_mode_notice_wording(self):
        notice = safe_mode_notice("main.py")
        assert notice == (
            "Drafter noticed that main.py is in a large or broad folder.\n"
            "For safety, live reload will watch your program and files used by\n"
            "your site rather than the entire folder."
        )


# ---------------------------------------------------------------------------
# WatchSet dynamics
# ---------------------------------------------------------------------------


class TestWatchSet:
    def test_add_served_file_sets_changed_event(self, tmp_path):
        main = make_project(tmp_path)
        helpers = tmp_path / "helpers.py"
        helpers.write_text("x = 1", encoding="utf-8")
        watch_set = WatchSet([WatchedPath(main, False)])
        assert not watch_set.changed.is_set()
        assert watch_set.add_watched_file(helpers)
        assert watch_set.changed.is_set()
        assert helpers.resolve() in watch_set.roots()

    def test_duplicate_add_is_rejected(self, tmp_path):
        main = make_project(tmp_path)
        watch_set = WatchSet([WatchedPath(main, False)])
        assert not watch_set.add_watched_file(main)

    def test_file_under_watched_directory_is_rejected(self, tmp_path):
        helpers = tmp_path / "helpers.py"
        helpers.write_text("x = 1", encoding="utf-8")
        watch_set = WatchSet([WatchedPath(tmp_path, False)])
        assert not watch_set.add_watched_file(helpers)

    def test_ignored_file_is_rejected(self, tmp_path):
        log = tmp_path / "notes.log"
        log.write_text("x", encoding="utf-8")
        rules = IgnoreRules(base_directory=tmp_path, patterns=("*.log",))
        watch_set = WatchSet([], ignore_rules=rules)
        assert not watch_set.add_watched_file(log)
        assert not watch_set.add_watched_file(tmp_path / DEBUG_LOG_FILENAME)

    def test_missing_file_is_rejected(self, tmp_path):
        watch_set = WatchSet([])
        assert not watch_set.add_watched_file(tmp_path / "ghost.py")

    def test_restart_targets_follow_full_reload_flag(self, tmp_path):
        main = make_project(tmp_path)
        other = tmp_path / "style.css"
        other.write_text("body {}", encoding="utf-8")
        watch_set = WatchSet([WatchedPath(main, False), WatchedPath(other, True)])
        assert watch_set.restart_targets() == {main.resolve()}


# ---------------------------------------------------------------------------
# Integration with make_app / serve_app_once
# ---------------------------------------------------------------------------


@pytest.fixture
def injected_system():
    def inject(system):
        _set_system_for_testing(system)
        return system

    yield inject
    _reset_system_for_testing()


class TestMakeAppIntegration:
    def test_normal_project_prints_no_notice(self, tmp_path, injected_system, capsys):
        main = make_project(tmp_path)
        system = injected_system(make_system(str(main)))
        app_server.make_app(system, MagicMock(), None)
        assert "large or broad folder" not in capsys.readouterr().out

    def test_safe_mode_prints_notice_and_tracks_serving(
        self, tmp_path, injected_system, capsys, monkeypatch
    ):
        main = make_project(tmp_path)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        system = injected_system(make_system(str(main)))
        app = app_server.make_app(system, MagicMock(), None)
        out = capsys.readouterr().out
        assert "Drafter noticed that main.py is in a large or broad folder." in out
        assert app.state.watch_plan.safe_mode
        # The user-files mount tracks served files in safe mode.
        mounts = [
            route.app
            for route in app.routes
            if getattr(route, "name", None) == "user_files"
        ]
        assert mounts and isinstance(mounts[0], app_server.TrackingStaticFiles)

    def test_reloader_disabled_skips_served_file_tracking(
        self, tmp_path, injected_system, monkeypatch
    ):
        main = make_project(tmp_path)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        system = injected_system(make_system(str(main), use_reloader=False))
        app = app_server.make_app(system, MagicMock(), None)
        mounts = [
            route.app
            for route in app.routes
            if getattr(route, "name", None) == "user_files"
        ]
        assert mounts and not isinstance(mounts[0], app_server.TrackingStaticFiles)

    def test_served_file_lands_in_watch_set(
        self, tmp_path, injected_system, monkeypatch
    ):
        main = make_project(tmp_path)
        helpers = tmp_path / "helpers.py"
        helpers.write_text("x = 1", encoding="utf-8")
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        system = injected_system(make_system(str(main)))
        app = app_server.make_app(system, MagicMock(), None)
        mount = next(
            route.app
            for route in app.routes
            if getattr(route, "name", None) == "user_files"
        )
        mount.on_serve(helpers)
        assert helpers.resolve() in app.state.watch_set.roots()

    def test_generated_log_never_joins_watch_set(
        self, tmp_path, injected_system, monkeypatch
    ):
        main = make_project(tmp_path)
        log = tmp_path / DEBUG_LOG_FILENAME
        log.write_text("boom", encoding="utf-8")
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        system = injected_system(make_system(str(main)))
        app = app_server.make_app(system, MagicMock(), None)
        assert not app.state.watch_set.add_watched_file(log)


class TestUseReloaderLifecycle:
    def run_server(self, system, monkeypatch):
        """Run serve_app_once with uvicorn stubbed out; report watcher use."""
        watcher_started = []

        async def fake_watch_and_reload(hub, watch_set, system, student_path):
            watcher_started.append(True)

        async def fake_serve(self):
            # Yield once so a created watcher task gets a chance to run.
            await asyncio.sleep(0)

        monkeypatch.setattr(app_server, "_watch_and_reload", fake_watch_and_reload)
        monkeypatch.setattr(app_server.uvicorn.Server, "serve", fake_serve)
        app_server.serve_app_once(system, MagicMock(), None)
        return watcher_started

    def test_use_reloader_false_never_starts_watcher(
        self, tmp_path, injected_system, monkeypatch
    ):
        main = make_project(tmp_path)
        system = injected_system(make_system(str(main), use_reloader=False))
        assert self.run_server(system, monkeypatch) == []

    def test_use_reloader_true_starts_watcher(
        self, tmp_path, injected_system, monkeypatch
    ):
        main = make_project(tmp_path)
        system = injected_system(make_system(str(main)))
        assert self.run_server(system, monkeypatch) == [True]
