import inspect
import os
import subprocess
import sys
from pprint import pprint


def main(module=sys.modules["__main__"]):
    program_name, *all_args = sys.argv
    command, args = None, []
    commands = module_functions(module)

    program_name = os.path.basename(program_name)
    command_name = program_name.replace("-", "_")
    command = commands.get(command_name)

    if not command:
        if len(all_args) == 0 or all_args in (["help"], ["-h"], ["--help"]):
            help(program_name, commands)
            exit(1)
        command_name, *args = all_args
        command_name = command_name.replace("-", "_")
        command = commands.get(command_name)
        if command_name == "help" or args in (["-h"], ["--help"]):
            if command_name == "help":
                command_name = args[0]
            print_command_help(command_name, commands.get(command_name))
            exit(0)

    if not command:
        print(f"error: no command named {command_name}", file=sys.stderr)
        exit(1)
    try:
        result = command(*args)
        if result is not None:
            pprint(result)
    except subprocess.CalledProcessError as err:
        exit(err.returncode)


def help(program_name, commands):
    print(f"usage: {program_name} <command> [<args>]\n")
    print("Available commands:")
    for cmd, f in commands.items():
        print_command_help(cmd, f)


def print_command_help(cmd, f):
    if f and f.__doc__:
        print(f"  \033[1m{cmd}\033[0m{inspect.signature(f)}")
        print(f"    {f.__doc__}")


def module_functions(module):
    return {
        name: func
        for name, func in inspect.getmembers(module, inspect.isfunction)
        if inspect.getmodule(func) == module
    }


def run(command, *args, check=True, env=None, cwd=None, capture_output=False):
    if isinstance(command, str):
        command = command.split()
    kwargs = {}
    if capture_output:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    return subprocess.run(command + list(args), check=check, env=env, cwd=cwd, **kwargs)


def sh(command, env=None):
    return subprocess.run(command, check=True, shell=True, env=env)


def exec(command, *args):
    if isinstance(command, str):
        command = command.split()
    os.execvp(command[0], command + list(args))


def output(command, *args, encoding="ascii"):
    if isinstance(command, str):
        command = command.split()
    return subprocess.check_output(command + list(args), encoding=encoding)


def lines(*args, **kwargs):
    return output(*args, **kwargs).splitlines()
