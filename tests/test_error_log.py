"""Tests for the shared debug log (app/error_log.py) and its endpoint.

The development server appends browser error reports to a JSON Lines file
next to the student's code. The log records environment details, trims
itself when it grows too large, and treats write failures as best-effort
(one CLI message, never an exception).
"""

import asyncio
import json
from types import SimpleNamespace

import pytest

import drafter.app.error_log as error_log
from drafter.app.error_log import (
    DEBUG_LOG_FILENAME,
    append_error_log_entry,
    build_log_entry,
    get_debug_log_path,
)


@pytest.fixture(autouse=True)
def reset_announcement_flag():
    """Each test starts with the one-time failure message unannounced."""
    error_log._write_failure_announced = False
    yield
    error_log._write_failure_announced = False


def read_entries(directory):
    path = get_debug_log_path(directory)
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class TestBuildLogEntry:
    def test_combines_client_payload_with_server_environment(self):
        entry = build_log_entry({"reports": [{"id": "x"}]}, "main.py")

        assert entry["main_file"] == "main.py"
        assert entry["client"] == {"reports": [{"id": "x"}]}
        assert entry["server"]["drafter_version"]
        assert entry["server"]["python_version"]
        assert entry["server"]["platform"]
        assert entry["timestamp"]


class TestAppendErrorLogEntry:
    def test_appends_json_lines(self, tmp_path):
        assert append_error_log_entry(tmp_path, {"n": 1})
        assert append_error_log_entry(tmp_path, {"n": 2})

        entries = read_entries(tmp_path)
        assert [entry["n"] for entry in entries] == [1, 2]

    def test_shared_filename_is_stable(self, tmp_path):
        append_error_log_entry(tmp_path, {"n": 1})
        assert (tmp_path / DEBUG_LOG_FILENAME).exists()

    def test_trims_oldest_entries_when_too_large(self, tmp_path, monkeypatch):
        monkeypatch.setattr(error_log, "MAX_LOG_BYTES", 400)
        monkeypatch.setattr(error_log, "TRIM_TARGET_BYTES", 200)

        for index in range(20):
            assert append_error_log_entry(tmp_path, {"n": index, "pad": "x" * 20})

        entries = read_entries(tmp_path)
        numbers = [entry["n"] for entry in entries]
        # The newest entry always survives; the oldest ones are dropped.
        assert numbers[-1] == 19
        assert 0 not in numbers
        assert get_debug_log_path(tmp_path).stat().st_size <= 400

    def test_write_failure_announces_once_and_returns_false(self, tmp_path, capsys):
        # A directory that does not exist makes the append fail.
        missing = tmp_path / "nope" / "nothere"

        assert append_error_log_entry(missing, {"n": 1}) is False
        assert append_error_log_entry(missing, {"n": 2}) is False

        output = capsys.readouterr().out
        assert output.count("could not write to its debug log") == 1

    def test_unserializable_entries_do_not_crash(self, tmp_path):
        # default=str covers values json cannot encode natively.
        assert append_error_log_entry(tmp_path, {"when": object()})
        assert read_entries(tmp_path)[0]["when"]


class TestRecordErrorLogEndpoint:
    def make_request(self, tmp_path, body: bytes):
        from drafter.app.app_server import record_error_log

        app = SimpleNamespace(
            state=SimpleNamespace(
                system=SimpleNamespace(
                    bootstrap=SimpleNamespace(get_main_filename=lambda: "main.py")
                ),
                user_directory=tmp_path,
            )
        )

        async def read_body():
            return body

        request = SimpleNamespace(app=app, body=read_body)
        return asyncio.run(record_error_log(request))

    def test_valid_report_is_written(self, tmp_path):
        payload = {"kind": "drafter-error-report", "reports": [{"id": "x"}]}
        response = self.make_request(tmp_path, json.dumps(payload).encode("utf-8"))

        assert response.status_code == 200
        entries = read_entries(tmp_path)
        assert len(entries) == 1
        assert entries[0]["client"] == payload
        assert entries[0]["main_file"] == "main.py"

    def test_invalid_json_is_rejected(self, tmp_path):
        response = self.make_request(tmp_path, b"{nope")
        assert response.status_code == 400
        assert not get_debug_log_path(tmp_path).exists()

    def test_non_object_report_is_rejected(self, tmp_path):
        response = self.make_request(tmp_path, b'["list"]')
        assert response.status_code == 400

    def test_oversized_report_is_rejected(self, tmp_path):
        from drafter.app.app_server import MAX_ERROR_REPORT_BYTES

        response = self.make_request(tmp_path, b"x" * (MAX_ERROR_REPORT_BYTES + 1))
        assert response.status_code == 413
        assert not get_debug_log_path(tmp_path).exists()
