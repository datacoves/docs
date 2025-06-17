import shlex
import subprocess

from projects.exceptions import SQLHookException
from projects.runners import utils


def _run_script(cmd_list):
    """
    Run a connection test.
    """
    try:
        subprocess.check_output(cmd_list)
    except subprocess.CalledProcessError as e:
        stderr = e.output.decode("utf-8")
        raise SQLHookException(stderr)
    except subprocess.TimeoutExpired:
        raise SQLHookException("SQL hook timed out. Please check host")


def run_on_sql_runner(connection: dict, script: str, runner: str):
    connection_b64 = utils.get_connection_b64(connection)
    script_b64 = utils.get_script_b64(script)
    cmd_list = shlex.split(
        f"/bin/bash -c 'source ${utils.SQL_RUNNERS_VIRTUALENVS[runner]}/bin/activate && python\
              projects/runners/run_on_{runner}.py {connection_b64} {script_b64}'"
    )
    return _run_script(cmd_list)
