#!/usr/bin/python

import os
import shutil
import json
from pathlib import Path


def generate_keys():
    """Generate ssh keys"""

    output_folder = Path("/config/.ssh")
    keys_file = Path("/opt/datacoves/user/ssh_keys.json")

    if keys_file.exists():
        shutil.rmtree(output_folder, ignore_errors=True)
        output_folder.mkdir(parents=True, exist_ok=True)
        os.chown(output_folder, 1000, 1000)
        data = json.load(open(keys_file))
        for key in data:
            private_path = output_folder / f"id_{key['key_type']}"
            print(f"Generating {private_path}...")
            with open(private_path, "w") as private_file:
                private_file.write(key["private"])

            public_path = output_folder / f"id_{key['key_type']}.pub"
            print(f"Generating {public_path}...")
            with open(public_path, "w") as public_file:
                public_file.write(key["public"])

            os.chown(private_path, 1000, 1000)
            os.chmod(private_path, 0o600)
            os.chown(public_path, 1000, 1000)


if __name__ == "__main__":
    generate_keys()
