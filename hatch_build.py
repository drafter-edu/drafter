import subprocess, shutil, os, pathlib
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


def _find_npm():
    # Try common names on Windows and POSIX
    for candidate in ("npm", "npm.cmd", "npm.exe"):
        p = shutil.which(candidate)
        if p:
            return p
    return None


class CustomHook(BuildHookInterface):
    def initialize(self, version, build_data):
        repo = pathlib.Path(__file__).parent
        js = repo / "js"
        out = repo / "src" / "drafter" / "assets" / "js"
        out.mkdir(parents=True, exist_ok=True)

        # 1) Build JS
        print("Building JS assets...")

        npm = _find_npm()
        if not npm:
            raise RuntimeError(
                "Node.js/npm is required to build the frontend but was not found on PATH.\n"
                "Install Node.js (LTS) and ensure npm is available in your shell, then retry.\n"
                "On Windows, PATH typically includes: C:\\Program Files\\nodejs\\"
            )

        if not (js / "package-lock.json").exists():
            # You can switch to install for devs without lockfile
            # or keep failing with a clearer message.
            # raise RuntimeError("package-lock.json not found; required for `npm ci`.")
            cmd = [npm, "install"]
        else:
            cmd = [npm, "ci"]
        subprocess.run(cmd, cwd=js, check=True)
        subprocess.run([npm, "run", "update"], cwd=js, check=True)
        subprocess.run([npm, "run", "build"], cwd=js, check=True)

        # 2) Copy artifacts
        built = js / "dist"
        for p in built.glob("*"):
            shutil.copy2(p, out / p.name)

        # 3) Ensure Skulpt runtime files exist in assets
        skulpt_dir = os.environ.get("SKULPT_DIR")
        needed = ["skulpt.js", "skulpt-stdlib.js", "skulpt.js.map"]
        if skulpt_dir:
            for name in needed:
                src = pathlib.Path(skulpt_dir) / name
                if not src.exists():
                    raise RuntimeError(f"Required Skulpt file not found: {src}")
                shutil.copy2(src, out / name)
        else:
            # No SKULPT_DIR provided. If files are already present (e.g., placed by `npm run update`), keep them.
            missing = [name for name in needed if not (out / name).exists()]
            if missing:
                raise RuntimeError(
                    "SKULPT_DIR is not set and the following Skulpt assets are missing: "
                    + ", ".join(missing)
                    + "\nSet SKULPT_DIR to a directory containing Skulpt build artifacts or run `npm run update` in js/."
                )
