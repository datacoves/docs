import asyncio

import pytest
from integration_tests.user_settings.base import git_ssh_key_test_connection
from integration_tests.workbench.base import (
    WorkbenchBase,
    WorkbenchServicesEnum,
    utils_test,
)
from playwright.async_api import expect

data = {
    "git_repo_ssh_url": "git@github.com:datacoves/balboa.git",
    "db_name": "test_db_name",
    "db_conn_template": "1",
    "db_auth_type": "key",
    "db_user": utils_test.secrets["snowflake_service_account"]["template_db_user"],
    "db_password": utils_test.secrets["snowflake_service_account"][
        "template_db_password"
    ],
}


class WorkbenchDocsTest(WorkbenchBase):
    def setUp(self):
        self._subpath = f"workbench/{__name__}"
        return super().setUp()

    @pytest.mark.asyncio
    async def test_workbench_docs(self):
        """
        Test that ensures Docs are accessible in the Workbench

        Steps:
            1. Login
            2. Go to Launchpad
            3. Go to Projects admin and enable Project by creating a SSH Key and testing it
            5. Go to Launchpad and Workbench
            6. Go to Observe
            7. Assert both docs and local-dbt-docs are visible
        """

        try:
            await self.asyncSetUp()

            user_session = await self.user_session()
            user = user_session["user"]
            await self.cluster_setup(user=user)

            await self.go_to_launchpad(user.email, user_session["password"])

            btn_open_user_menu = self.page.get_by_role("button", name="Open user menu")
            await btn_open_user_menu.wait_for(state="attached")
            await btn_open_user_menu.evaluate("el => el.click()")
            await self.page.get_by_role("menuitem", name="Settings").click()
            await self.page.get_by_role("heading", name="Profile Settings").wait_for()
            await self.screenshot()

            await self.git_ssh_key_gen()
            await self.enable_project()
            await self.enable_environment_service(
                service=WorkbenchServicesEnum.DOCS, needs_extra_config=True
            )
            await self.configure_docs_stack()
            await self.go_to_observe_tab()
            print("Workbench Docs completed")

        except Exception:
            pods = [
                ("pomerium",),
                ("airflow-webserver",),
                ("airflow-scheduler", "s3-sync"),
                ("airflow-scheduler", "scheduler"),
                ("airflow-postgresql",),
            ]
            await self.dump_pod_logs(pods=pods)
            raise

        finally:
            await self.asyncTearDown()

    async def git_ssh_key_gen(self):
        """Test generate ssh key to clone git repository"""
        await self.page.get_by_role("tab", name="Git SSH Keys").click()
        await self.page.locator("section").filter(
            has_text="Git SSH keysAdd this SSH key to your git server account to clone your repos."
        ).get_by_role("button", name="Add").click()
        await self.page.get_by_role("menuitem", name="Auto-generate key pairs").click()
        await self.clean_toast()
        await self.page.get_by_role("button", name="COPY").click()
        await expect(
            self.page.get_by_text("SSH key copied to clipboard")
        ).to_be_visible()
        await self.clean_toast()
        await git_ssh_key_test_connection(
            page=self.page,
            git_repo_ssh_url=data["git_repo_ssh_url"],
            is_success=True,
            ssh_key_title=self.ssh_key_title,
        )
        await self.page.screenshot()
        await self.clean_toast()
        await self.page.goto(f"https://{self.domain}/launchpad")

    async def configure_docs_stack(self):
        await self.page.get_by_role("tab", name="Docs settings").click()
        await self.page.get_by_label("Git branch name*").fill("dbt-docs")
        await self.screenshot()
        await self.page.get_by_role("button", name="Save Changes").click()
        await self.page.get_by_role(
            "row", name="Analytics Development 0 service connections"
        ).wait_for(state="attached")
        await self.screenshot()

    async def go_to_observe_tab(self):
        await self.get_into_workbench(service=WorkbenchServicesEnum.DOCS)

        # TO avoid the error: Nightly Can't Open This Page (Pomerium is not ready)
        await asyncio.sleep(120)
        await self.page.get_by_text("Observe").click()
        await expect(
            self.page.frame_locator('iframe[name="observe"]').get_by_role(
                "heading", name="DBT Docs not generated yet"
            )
        ).to_be_visible()
        await self.screenshot()
        await self.page.get_by_role("button", name="Docs", exact=True).click()
        await expect(
            self.page.frame_locator('iframe[name="observe"]').get_by_role(
                "heading", name="Datacoves Demo"
            )
        ).to_be_visible()
        await self.screenshot()
