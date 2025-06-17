import asyncio
import re
from enum import Enum

from integration_tests.base_test import PlaywrightChannelsTestCase, utils_test


class WorkbenchServicesEnum(Enum):
    AIRFLOW = "ORCHESTRATE"
    AIRBYTE = "LOAD"
    SUPERSET = "ANALYZE"
    DOCS = "OBSERVE > Docs"


class WorkbenchBase(PlaywrightChannelsTestCase):
    async def go_to_launchpad(self, email: str = None, password: str = None):
        # Login
        if email and password:
            await utils_test.login(
                page=self.page,
                username=email,
                password=password,
                domain=self.domain,
            )

        await self.page.goto(f"https://{self.domain}/launchpad")
        btn_open_env = self.page.get_by_role("button", name="Open", exact=True)
        await btn_open_env.wait_for(
            state="attached", timeout=self.get_timeout(minutes=5)
        )
        await self.screenshot(delay=2)

    async def get_into_workbench(self, service: WorkbenchServicesEnum):
        await self.go_to_launchpad()
        btn_open_env = self.page.get_by_role("button", name="Open", exact=True)
        await btn_open_env.wait_for(
            state="attached", timeout=self.get_timeout(minutes=5)
        )

        # Wait for service pods to start
        if service == WorkbenchServicesEnum.AIRBYTE:
            time_sleep = 300
        else:
            time_sleep = 240

        await asyncio.sleep(time_sleep)  # Increase if it's needed
        await btn_open_env.click()
        await self.page.frame_locator('iframe[name="docs"]').get_by_role(
            "heading", name="Welcome to the Datacoves Documentation"
        ).wait_for(state="attached", timeout=self.get_timeout(minutes=7))
        await self.screenshot()

    async def enable_project(self):
        """Change Repo cloning to SSH, add key to Github, and test Project connection"""
        await self.page.get_by_role("link", name="Projects").click()
        await self.page.wait_for_selector(
            "button.chakra-button.css-d99nyo", state="visible"
        )
        project_edit_button = (
            self.page.get_by_role("cell", name="Test").get_by_role("button").nth(1)
        )
        await project_edit_button.wait_for(state="visible")
        await project_edit_button.wait_for(state="attached")
        await self.screenshot()
        await project_edit_button.evaluate("el => el.click()")
        clone_strategy_combobox = self.page.get_by_role(
            "combobox", name="Clone strategy"
        )
        await clone_strategy_combobox.is_visible()
        await clone_strategy_combobox.select_option("ssh_clone")
        await self.screenshot()
        develop_ssh = await self.page.get_by_text("ssh-ed25519").input_value()
        await utils_test.github_ssh_key_create(self.ssh_key_title, develop_ssh)
        btn_save = self.page.get_by_role("button", name="Save Changes")
        await btn_save.wait_for(state="visible")
        await btn_save.wait_for(state="attached")
        await btn_save.evaluate("el => el.click()")
        await self.screenshot()
        await self.page.get_by_role("cell", name="connection template").wait_for(
            state="attached", timeout=self.get_timeout(minutes=1)
        )
        await self.screenshot()
        print("Project successfully tested")

    async def enable_environment_service(
        self, service: WorkbenchServicesEnum, needs_extra_config=False
    ):
        await self.page.get_by_role("link", name="Environments").click()
        await self.page.get_by_role(
            "row", name="Analytics Development 0 service connections"
        ).get_by_role("button").first.click()
        await self.page.get_by_role("tab", name="Stack Services").click()

        if service != WorkbenchServicesEnum.DOCS:
            # Turn VSCode off we do not need it.
            await self.page.locator("div").filter(
                has_text=re.compile(
                    r"^TRANSFORM \+ OBSERVE > Local DocsPowered by VS Code and dbt$"
                )
            ).locator("span").nth(1).click()

        await self.page.get_by_role("group").filter(has_text=service.value).locator(
            "span"
        ).nth(1).click()
        await self.screenshot()
        await self.page.get_by_role("tab", name="General settings").click()
        await self.page.get_by_label("dbt profile name").fill("default")

        if not needs_extra_config:
            await self.page.get_by_role("button", name="Save Changes").click()
            await self.page.get_by_role(
                "row", name="Analytics Development 0 service connections"
            ).wait_for(state="attached")
            await self.screenshot()
