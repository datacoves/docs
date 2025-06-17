#!/usr/bin/python

import json
import os
import stat
import subprocess
from pathlib import Path


def generate_files():
    """Generate profile files and executes them if configured so"""

    files_path = Path("/opt/datacoves/user/files.json")
    cloned_repo = Path("/config/workspace/.git").exists()

    if files_path.exists():
        files = json.load(open(files_path))
        for file in files:
            path_output = subprocess.run(
                f"echo {file['mount_path']}", shell=True, capture_output=True
            )
            mount_path = path_output.stdout.decode().replace("\n", "")
            if not mount_path.startswith("/config/workspace") or cloned_repo:
                mount_path = Path(mount_path)
                if file["override"] or not mount_path.exists():
                    mount_path.parent.mkdir(parents=True, exist_ok=True)
                    os.chown(mount_path.parent, 1000, 1000)

                    with open(mount_path, "w") as target_file:
                        target_file.write(file["content"])
                    os.chmod(mount_path, int(file["permissions"], 8))
                    os.chown(mount_path, 1000, 1000)
                    if file["content"].startswith("#!"):
                        st = os.stat(mount_path)
                        os.chmod(mount_path, st.st_mode | stat.S_IEXEC)

                    if file["execute"]:
                        print(f"Executing {mount_path}...")
                        output = subprocess.run(
                            ["/usr/bin/perl", mount_path],
                            env=os.environ,
                            cwd=mount_path.parent,
                        )
                        if output.stderr:
                            print(output.stdout)
                    else:
                        print(f"Generating {mount_path}...")
            else:
                print(f"Skipping {mount_path} as workspace not initialited yet...")


if __name__ == "__main__":
    generate_files()
