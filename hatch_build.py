import subprocess, shutil, os, pathlib
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomHook(BuildHookInterface):
    def initialize(self, version, build_data):
        repo = pathlib.Path(__file__).parent
        js = repo / "js"
        out = repo / "src" / "drafter" / "assets"
        out.mkdir(parents=True, exist_ok=True)

        # 1) Build JS
        subprocess.run(["npm", "ci"], cwd=js, check=True)
        subprocess.run(["npm", "run", "build"], cwd=js, check=True)

        # 2) Copy artifacts
        built = js / "dist"
        for p in built.glob("*"):
            shutil.copy2(p, out / p.name)

        # 3) Vendor skulpt
        shutil.copy2(js / "vendor" / "skulpt.js", out / "skulpt.js")
        shutil.copy2(js / "vendor" / "skulpt-stdlib.js", out / "skulpt-stdlib.js")
