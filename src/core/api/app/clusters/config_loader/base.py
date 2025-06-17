"""
Base class for both kinds of configuration loader, to provide common
features such as diffing.
"""

import difflib
import json
import logging
from enum import Enum

from clusters.adapters import EnvironmentAdapter
from core.models import DatacovesModel

logger = logging.getLogger(__name__)


class DiffEnum(Enum):
    NO_CHANGES = 0
    APPLY_CHANGES = 1
    DO_NOT_APPLY_CHANGES = 2


class BaseConfigLoader:
    @classmethod
    def _get_configuration_diff(
        cls,
        current_name: str,
        current_value: any,
        source_name: str,
        source_value: any,
        req_user_confirm: bool,
    ) -> DiffEnum:
        """Look for the differences between two sources

        Args:
            current_name (str): Name of the current value
            current_value (any): Current value
            source (str): Name of the new value
            source_value (any): New value
            req_user_confirm (bool): Require user confirmation? Used by tests

        Returns:
            DiffEnum: Return strategy to apply changes
        """

        if isinstance(current_value, dict):
            current_value = json.dumps(
                current_value, sort_keys=True, indent=4, separators=(",", ": ")
            )
            source_value = json.dumps(
                source_value, sort_keys=True, indent=4, separators=(",", ": ")
            )

        elif not isinstance(current_value, str):
            current_value = str(current_value)
            source_value = str(source_value)

        diff = difflib.unified_diff(
            current_value.splitlines(),
            source_value.splitlines(),
            fromfile=current_name,
            tofile=source_name,
            lineterm="",
            n=1,
        )

        diff = list(filter(lambda x: not x.startswith("@@"), diff))
        if diff:
            if req_user_confirm:
                from rich.console import Console
                from rich.prompt import Confirm

                console = Console()
                for line in diff:
                    if line.startswith("+"):
                        line = f"[green]{line}[/green]"
                    elif line.startswith("-"):
                        line = f"[red]{line}[/red]"
                    console.print(line)

                confirm = Confirm.ask(
                    f"Do you want to overwrite {current_name}?", default=False
                )
                return (
                    DiffEnum.APPLY_CHANGES if confirm else DiffEnum.DO_NOT_APPLY_CHANGES
                )

            return DiffEnum.APPLY_CHANGES  # E.g. Integrantion test

        return DiffEnum.NO_CHANGES

    @classmethod
    def _generate_model_name(cls, model: DatacovesModel) -> str:
        model_name = model.__class__.__name__

        if hasattr(model, "slug"):
            model_name += f" {model.slug}"
        else:
            model_name += f" {model.id}"

        return model_name

    @classmethod
    def _update_config(
        cls,
        model: DatacovesModel,
        env_config: dict,
        created: bool,
        source: str,
        req_user_confirm: bool,
    ):
        """Update model config."""
        model_name = cls._generate_model_name(model)

        for key, value in env_config.items():
            apply_changes = DiffEnum.APPLY_CHANGES

            if not created:
                apply_changes = cls._get_configuration_diff(
                    current_name=model_name,
                    current_value=getattr(model, key),
                    source_name=source,
                    source_value=value,
                    req_user_confirm=req_user_confirm,
                )

            if apply_changes == DiffEnum.APPLY_CHANGES:
                setattr(model, key, value)

    @classmethod
    def _validate_config_diff(
        cls,
        model: DatacovesModel,
        adapter: EnvironmentAdapter,
        source_config: any,
        source: str,
        req_user_confirm: bool,
    ) -> DiffEnum:
        """This is for diffing against the default configuration based on
        an adapter.  I made it generic like I made everything else, but it
        probably is only useful for environments.
        """

        current_config = adapter.get_default_config(model)
        new_config = adapter.get_default_config(model, source_config)

        model_name = f"{adapter.service_name} config " + cls._generate_model_name(model)

        return cls._get_configuration_diff(
            current_name=model_name,
            current_value=current_config,
            source_name=source,
            source_value=new_config,
            req_user_confirm=req_user_confirm,
        )
