import glob
import os
import re
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOCKERFILE_PATHS = [
    BASE_DIR / "src/code-server/code-server/Dockerfile",
    BASE_DIR / "src/code-server/dbt-core-interface/Dockerfile",
    BASE_DIR / "src/airflow/airflow/Dockerfile",
    BASE_DIR / "src/ci/airflow/Dockerfile",
    BASE_DIR / "src/ci/basic/Dockerfile",
]
REQUIREMENTS_COMMON_BASE = BASE_DIR / "src/common/requirements"
CODE_SERVER_EXTENSIONS_BASE = BASE_DIR / "src/code-server/code-server/profiles"
REQUIREMENTS_AIRFLOW_PROVIDERS_BASE = BASE_DIR / "src/common/providers"


console = Console()


def extract_labels_from_dockerfiles(filepath: Path, label_pattern: str):
    """
    Extracts labels from a Dockerfile based on the provided label pattern.

    Args:
        filepath (Path): The path to the Dockerfile.
        label_pattern (str): The regex pattern to match the labels.

    Returns:
        dict: A dictionary where the keys are the label names and the values are their versions.

    Raises:
        SystemExit: If the Dockerfile does not exist, the script exits with a status code of 1.
    """
    if not filepath.exists():
        dockerfile = filepath.relative_to(BASE_DIR)
        print(f"Error: {dockerfile} does not exist.")
        sys.exit(1)

    labels = {}
    dockerfile_content = filepath.read_text(encoding="utf-8")

    folder_name = filepath.parent.name
    if "src/ci" in str(filepath.absolute()):
        folder_name = f"ci-{folder_name}"

    pattern = re.compile(label_pattern)
    matches = pattern.findall(dockerfile_content)
    for lib, version in matches:
        labels[lib] = version

    return labels


def extract_requirements(filepath_base: str):
    """
    Extracts the list of required libraries and their versions from the requirements files.

    This function reads all files in the specified base directory, extracts the library names and versions,
    and returns them in a dictionary. If any errors occur during the processing of the files, they are collected
    and printed, and the script exits with a status code of 1.

    Args:
        filepath_base (str): The base directory containing the requirements files.

    Returns:
        dict: A dictionary where the keys are the library names and the values are their versions.

    Raises:
        SystemExit: If any errors occur during the processing of the files, the script exits with a status code of 1.
    """
    requirements = {}
    req_errors = []

    # Iterate over all files in the specified base directory
    for filename in os.listdir(filepath_base):
        filepath = os.path.join(filepath_base, filename)

        # Check if the current path is a file
        if os.path.isfile(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                # Read each line in the file
                for line in f.readlines():
                    req_file = Path(filepath).relative_to(BASE_DIR)
                    line_sanitized = line.strip()

                    # Skip lines that start with "-r"
                    if line.startswith("-r"):
                        continue

                    try:
                        # Correctly separate the library and the version
                        library, version = re.split(r"==|~=|@|>=", line_sanitized)
                        requirements[library] = version
                    except ValueError:
                        # Collect errors for lines with incorrect format
                        req_errors.append(
                            f"Version not found or incorrect format in line: "
                            f"[yellow bold]{line_sanitized}[/yellow bold] "
                            f"in [yellow]{req_file}[/yellow]"
                        )

    # If there are any errors, print them and exit with an error code
    if req_errors:
        errors = "\n".join(req_errors)
        panel = Panel(errors, style="red")
        console.print(panel, end=" ")
        sys.exit(1)

    return requirements


def dockerfile_validate_libraries():
    """
    Validates that the labels in Dockerfile have the correct format and match the requirements.txt.
    This function performs the following steps:
    1. Extracts the list of required libraries and their versions from the requirements file.
    2. Iterates over the specified Dockerfile paths.
    3. For each Dockerfile, constructs a label pattern based on the folder name.
    4. Extracts labels from the Dockerfile using the constructed pattern.
    5. Compares the extracted labels with the required libraries and their versions.
    6. Collects any discrepancies, such as missing libraries or version mismatches.
    7. If discrepancies are found, prints a table of mismatches and exits with an error code.
    Returns:
        None
    Raises:
        SystemExit: If any discrepancies are found between the Dockerfile labels and the requirements.
    """
    """Validates that the labels in Dockerfile have the correct format and match the requirements.txt."""

    libraries_with_error = []
    requirements = extract_requirements(filepath_base=REQUIREMENTS_COMMON_BASE)

    for filepath in DOCKERFILE_PATHS:
        folder_name = filepath.parent.name
        if "src/ci" in str(filepath.absolute()):
            folder_name = f"ci-{folder_name}"

        label_pattern = (
            rf"com\.datacoves\.library\.{folder_name}\.(\S+?)=([\w\.\-\[\]+]+)"
        )
        docker_labels = extract_labels_from_dockerfiles(
            filepath=filepath, label_pattern=label_pattern
        )
        dockerfile = filepath.relative_to(BASE_DIR)

        for lib, req_version in requirements.items():
            if lib not in docker_labels:
                print(docker_labels)
                print(lib, req_version)
                libraries_with_error.append(
                    [str(dockerfile), lib, req_version, "Missing"]
                )

            else:
                docker_version = docker_labels[lib]  # Get the version from requirements
                if req_version != docker_version:
                    libraries_with_error.append(
                        [str(dockerfile), lib, req_version, docker_version]
                    )

    if len(libraries_with_error) > 0:
        table = Table(
            "Dockerfile",
            "Library",
            "Req version",
            title="Dockerfile Libraries Missmatching",
        )
        table.add_column("Docker version", style="red")
        for dockerfile, library, req_version, docker_version in libraries_with_error:
            table.add_row(dockerfile, library, req_version, docker_version)

        console.print(table)
        sys.exit(1)


def extract_code_server_extensions():
    """
    Extracts and returns a dictionary of code-server extensions and their versions.

    This function searches for all `.vsix` files within the `CODE_SERVER_EXTENSIONS_BASE` directory
    and its subdirectories. It extracts the version from the filename and maps the extension name
    to its version in a dictionary. If any errors occur during the processing of the files, they
    are collected and printed, and the script exits with a status code of 1.

    Returns:
        dict: A dictionary where the keys are the extension names and the values are their versions.

    Raises:
        SystemExit: If any errors occur during the processing of the files, the script exits with a status code of 1.
    """

    def extract_code_server_extension_version(filename: str):
        """Extracts the version from the filename."""
        match = re.search(r"[\-\.]([\d\.]+)(?=\.[a-z]+$|$)", filename)
        if match:
            return match.group(1)
        return None

    extensions = {}
    extensions_errors = []

    # Use glob for more concise and efficient file searching
    for vsix_file in glob.glob(
        f"{CODE_SERVER_EXTENSIONS_BASE}/**/**/*.vsix"
    ):  # Recursive search
        try:
            filename = os.path.basename(vsix_file).replace(".vsix", "")
            version = extract_code_server_extension_version(filename)
            # Remove version and any trailing chars
            name = (
                filename.replace("-" + version, "")
                .replace("." + version, "")
                .replace("v" + version, "")
                .strip("_.")
            )
            extensions[name] = version

        except Exception as e:
            extensions_errors.append(f"Error processing {vsix_file}: {e}")

    if extensions_errors:
        # Print errors with a clear indicator
        errors = "\n".join(extensions_errors)
        panel = Panel(errors, style="red")
        console.print(panel, end=" ")
        sys.exit(1)

    return extensions


def dockerfile_validate_extensions():
    """Validates that the extensions in Dockerfile have the correct format and match the extracted extensions."""

    # Define the pattern to match the extension labels in the Dockerfile
    extension_pattern = r"com\.datacoves\.extension\.code-server\.([\w\.-]+)=([\w\.-]+)"
    filepath = DOCKERFILE_PATHS[0]
    dockerfile = filepath.relative_to(BASE_DIR)

    # Extract the labels from the Dockerfile
    docker_labels = extract_labels_from_dockerfiles(
        filepath=filepath, label_pattern=extension_pattern
    )

    # Extract the code-server extensions
    code_server_extensions = extract_code_server_extensions()

    extensions_with_error = []

    # Compare the extracted labels with the code-server extensions
    for ext_name_label, ext_label_version in docker_labels.items():
        if ext_name_label in code_server_extensions:
            ext_version = code_server_extensions[
                ext_name_label
            ]  # Get the version from requirements
            if ext_version != ext_label_version:
                extensions_with_error.append(
                    [str(dockerfile), ext_name_label, ext_version, ext_label_version]
                )

    # If there are any mismatches, print them in a table and exit with an error
    if len(extensions_with_error) > 0:
        table = Table(
            "Dockerfile",
            "Extension",
            "Ext version",
            title="Dockerfile Extensions Missmatching",
        )
        table.add_column("Docker version", style="red")
        for dockerfile, ext_name, ext_version, docker_version in extensions_with_error:
            table.add_row(dockerfile, ext_name, ext_version, docker_version)

        console.print(table)
        sys.exit(1)


def docker_validate_airflow_providers():
    """Validates that the Airflow providers in Dockerfile have the correct format and match the requirements."""

    # Define the pattern to match the provider labels in the Dockerfile
    provider_pattern = r"com\.datacoves\.provider\.airflow\.(\S+?)=([\w\.\-\[\]+]+)"
    filepath = DOCKERFILE_PATHS[2]
    dockerfile = filepath.relative_to(BASE_DIR)

    # Extract the labels from the Dockerfile
    docker_labels = extract_labels_from_dockerfiles(
        filepath=filepath, label_pattern=provider_pattern
    )

    # Extract the requirements for Airflow providers
    requirements = extract_requirements(
        filepath_base=REQUIREMENTS_AIRFLOW_PROVIDERS_BASE
    )

    providers_with_error = []

    # Check for missing providers in the Dockerfile
    for provider, provider_version in requirements.items():
        if provider not in docker_labels:
            providers_with_error.append(
                f"LABEL provider for [bold]{provider}[/bold] not found in {dockerfile}"
            )

    if providers_with_error:
        # Print errors with a clear indicator
        errors = "\n".join(providers_with_error)
        panel = Panel(errors, style="red")
        console.print(panel, end=" ")
        sys.exit(1)

    providers_with_error = []

    # Compare the extracted labels with the requirements
    for provider, provider_version in requirements.items():
        provider_docker_version = docker_labels[
            provider
        ]  # Get the version from requirements
        if provider_version != provider_docker_version:
            providers_with_error.append(
                [provider, provider_version, provider_docker_version]
            )

    # If there are any mismatches, print them in a table and exit with an error
    if len(providers_with_error) > 0:
        table = Table(
            "Provider",
            "Prov version",
            title=f"Airflow Providers Missmatching: {dockerfile}",
        )
        table.add_column("Docker version", style="red")
        for provider, prov_version, docker_version in providers_with_error:
            table.add_row(provider, prov_version, docker_version)

        console.print(table)
        sys.exit(1)


if __name__ == "__main__":
    dockerfile_validate_libraries()
    dockerfile_validate_extensions()
    docker_validate_airflow_providers()
