from pathlib import Path

from lib.config_files import load_file


def validate_config(path: Path):
    validate_cluster_config(path)
    for envdir in path.glob("environments/*"):
        validate_environment_config(envdir)


def validate_cluster_config(path):
    validate_file(path / "cluster-params.yaml", ClusterParamsConfig)
    validate_file(path / "pricing.yaml", PricingConfig, optional=True)
    validate_file(path / "secrets/core-api.env")
    validate_file(path / "docker-config.secret.json")


def validate_environment_config(path):
    validata_file(path / "environment.yaml", EnvironmentConfig)
    validata_file(path / "airflow.yaml", AirflowConfig, optional=True)
    validata_file(path / "airbyte.yaml", AirbyteConfig, optional=True)


def validate_file(path, schema=None, optional=False):
    if path.endswith(".env"):
        # TODO: Read env files data. For now, only validate it exists.
        assert not optional and path.exists(), f"Missing file {path}."
        return

    if optional and not path.exists():
        return

    data = load_file(path, optional=False)
    if schema:
        validate(data, schema)


def validate(data, schema):
    raise NotImplemented()
