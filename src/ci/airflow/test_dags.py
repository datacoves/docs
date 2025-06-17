import argparse
import ast
import os
import time
from pathlib import Path

from airflow.models import DagBag


class DatacovesFunctionVisitor(ast.NodeVisitor):
    def __init__(self, source_code):
        self.in_task_function = False
        self.variable_usage_outside_task = []
        self.source_code = source_code

    def visit_FunctionDef(self, node):
        # Check if the function is decorated with @task
        if any(
            (isinstance(decorator, ast.Name) and decorator.id == "task")
            or (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Name)
                and decorator.func.id == "task"
            )
            or (
                isinstance(decorator, ast.Attribute)
                and isinstance(decorator.value, ast.Name)
                and decorator.value.id == "task"
            )
            for decorator in node.decorator_list
        ):
            self.in_task_function = True
            self.generic_visit(node)
            self.in_task_function = False
        else:
            self.generic_visit(node)

    def visit_Name(self, node):
        if node.id == "Variable":
            if not self.in_task_function:
                self.variable_usage_outside_task.append((node.lineno, node.col_offset))
        self.generic_visit(node)


try:
    DAG_FOLDER = Path(os.environ["AIRFLOW__CORE__DAGS_FOLDER"])
except KeyError:
    raise Exception("AIRFLOW__CORE__DAGS_FOLDER environment variable not set.")

parser = argparse.ArgumentParser(description="Test Airflow DAGs.")
parser.add_argument(
    "--dag-loadtime-threshold",
    type=int,
    default=1,
    help="Threshold for DAG loading time in seconds.",
)
parser.add_argument(
    "--check-variable-usage",
    action="store_true",
    default=False,
    help="Check Variable usage outside @task decorated functions.",
)
parser.add_argument(
    "--write-output",
    action="store_true",
    default=False,
    help="Write the output to a file.",
)
parser.add_argument(
    "--filename",
    type=str,
    default="test_dags_results.md",
    help="Filename of the output file.",
)
args = parser.parse_args()

DAG_LOADTIME_THRESHOLD = args.dag_loadtime_threshold
CHECK_VARIABLE_USAGE = args.check_variable_usage
WRITE_OUTPUT = args.write_output
OUTPUT_FILENAME = args.filename
DAGBAG = DagBag()

dag_counter = 0
outputs = []
dag_files = [
    f
    for f in DAG_FOLDER.rglob("*.py")
    if f.is_file() and f.suffix == ".py" and "__init__.py" not in str(f)
]


def _detect_variable_usage_outside_taskflow(file_path):
    with open(file_path, "r") as file:
        source_code = file.read()
        tree = ast.parse(source_code, filename=file_path)

    visitor = DatacovesFunctionVisitor(source_code)
    visitor.visit(tree)

    return visitor.variable_usage_outside_task


for dag_file in dag_files:
    print(f"Loading {dag_file}")
    if CHECK_VARIABLE_USAGE:
        # Check for Variable usage outside @task decorated functions
        variable_usage_outside_task = _detect_variable_usage_outside_taskflow(dag_file)
        if variable_usage_outside_task:
            outputs.append(
                f"{dag_file} has Variable usage outside @task decorated functions at: "
                f"{variable_usage_outside_task}"
            )
    start = time.time()
    try:
        dag = DAGBAG.process_file(dag_file.absolute().as_posix(), only_if_updated=True)
    except ImportError as e:
        outputs.append(f"{dag_file} has an error: {e}")
    except KeyError:
        # KeyErrors at DagBag loading are due to missing Variables
        # this is expected in CI
        pass
    end = time.time()
    # Print a warning if the DAG took too long to load
    if end - start > DAG_LOADTIME_THRESHOLD:
        outputs.append(f"{dag_file} took {end - start:.5f} seconds to load.")
    dag_counter += 1

print(f"Parsed {dag_counter} DAGs.")


if outputs:
    print("Warnings found")
    print("\n".join(outputs))
if WRITE_OUTPUT:
    with open(OUTPUT_FILENAME, "w") as file:
        if outputs:
            file.write("⚠️ **Test Warnings Detected:**\n\n")
            for output in outputs:
                file.write(f"- {output}\n")
        else:
            file.write("No warnings found.")
        print(f"Results written to {os.getcwd()}/{OUTPUT_FILENAME}")
