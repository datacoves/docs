"""
Read and write config files. Most commonly used: load_file, write_yaml.
"""

import base64
import json
import re
import sys
from pathlib import Path

import yaml

from .dicts import deep_merge

### Directories ###


def mkdir(path):
    if not isinstance(path, Path):
        path = Path(path)
    path.mkdir(parents=True, exist_ok=True)


### Loading ###


def load_file(path, optional=True):
    if isinstance(path, Path):
        path = str(path)
    parts = path.rsplit(".", 1)
    prefix, suffix = parts if len(parts) == 2 else (parts[0], "yaml")
    loaders = {
        "yaml": load_yaml,
        "yml": load_yaml,
        "json": load_json,
        "env": load_env_file,
    }
    loader = loaders.get(suffix, load_yaml)

    path = Path(f"{prefix}.{suffix}")
    path_secret = Path(f"{prefix}.secret.{suffix}")
    path_local = Path(f"{prefix}.local.{suffix}")
    res = {}
    if path.is_file():
        config = loader(path)
        if config:
            res.update(config)
    elif not optional:
        raise FileNotFoundError(path)
    if path_secret.is_file():
        config = loader(path_secret)
        if config:
            res = deep_merge(config, res)
    if path_local.is_file():
        config = loader(path_local)
        if config:
            res = deep_merge(config, res)
    return res


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_env_file(path):
    env = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            env[name.strip()] = value.strip()
    return env


def load_as_base64(path):
    with open(path, "rb") as f:
        return str(base64.b64encode(f.read()), encoding="ascii")


def load_text_file(path):
    with open(path, "r") as f:
        return f.read()


### Writing ###


class YAMLDumper(yaml.Dumper):
    def ignore_aliases(*args):
        return True

    def increase_indent(self, flow=False, *args, **kwargs):
        return super().increase_indent(flow=flow, indentless=False)


def emit_yamls(dest_dir, files):
    for path, file_data in files.items():
        with open(dest_dir / path, "w+") as f:
            if isinstance(file_data, str):
                print(file_data, file=f)
            else:
                print_yamls(file_data, file=f)


def write_file(path, data):
    with open(path, "w+") as f:
        print(data, file=f)


def write_yaml(path, data):
    with open(path, "w+") as f:
        print_yamls(data, file=f)


def print_yamls(resources, file=sys.stdout):
    if isinstance(resources, dict):
        resources = [resources]
    first = True
    for res in resources:
        if not first:
            print("---", file=file)
        print(
            yaml.dump(res, default_flow_style=False, Dumper=YAMLDumper),
            end="",
            file=file,
        )
        first = False
    print(file=file)


### Update ###


def update_file(path, f):
    assert callable(f)
    contents = ""
    with open(path, "r", encoding="utf-8") as file:
        contents = file.read()
    new_contents = f(contents)
    with open(path, "w") as file:
        file.write(new_contents)


def replace_in_file(path, pattern, replacement):
    if not isinstance(pattern, re.Pattern):
        pattern = re.compile(pattern, flags=re.MULTILINE)
    update_file(path, lambda s: re.sub(pattern, replacement, s))


def secret_value_from_json(path, key, encode=False):
    with open(path, "r") as f:
        data = f.read()
        value = json.loads(data)[key]
        return (
            str(base64.b64encode(value.encode()), encoding="ascii") if encode else value
        )


def secret_value_from_yaml(path, key, encode=False):
    with open(path, "r") as f:
        data = f.read()
        value = yaml.load(data, Loader=yaml.FullLoader)[key]
        return (
            str(base64.b64encode(value.encode()), encoding="ascii") if encode else value
        )
