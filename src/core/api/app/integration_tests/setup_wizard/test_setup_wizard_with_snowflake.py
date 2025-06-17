import asyncio

import pytest
from integration_tests.base_test import utils_test
from integration_tests.setup_wizard.base import SetupWizardBase

data = {
    "account_name": "Acme Inc.",
    "first_project": "Commercial Analytics",
    "conn_type": "snowflake",
    "warehouse_account": "toa80779",
    "warehouse": "wh_integration",
    "database": "balboa_dev",
    "role": "bot_integration",
    "schema": "sebastian",
    "user": utils_test.secrets["snowflake_service_account"]["user"],
    "password": utils_test.secrets["snowflake_service_account"]["password"],
    "git_repo_ssh_url": "git@github.com:datacoves/balboa.git",
    "release_branch": "main",
}


class SetupWizardWithSnowflakeTest(SetupWizardBase):
    def setUp(self):
        self._subpath = f"setup_wizard/{__name__}"
        return super().setUp()

    @pytest.mark.asyncio
    async def test_setup_wizard_with_snowflake(self):
        """Test to setup an account with Snowflake"""

        try:
            await self.asyncSetUp()

            user_session = await self.user_session()
            user = user_session["user"]
            cluster = await self.cluster_setup_wizard()

            # Login
            await utils_test.login(
                page=self.page,
                username=user.email,
                password=user_session["password"],
                domain=cluster.domain,
            )

            await self.lauchpad_create_new_account()
            await self.setup_wizard_step_one(data=data)
            await self.setup_wizard_step_two(data=data)
            await self.setup_wizard_step_three()
            await self.setup_wizard_step_four(data=data)
            await self.setup_wizard_step_five()
            await self.setup_wizard_lauchpad(data=data)
            print("Setup wizard completed with Snowflake completed")

        except Exception:
            await self.dump_pod_logs()
            raise

        finally:
            await self.asyncTearDown()

    async def setup_wizard_step_three(self):
        """Complete the step three with Snowflake warehouse"""

        await asyncio.sleep(2)  # Wait until the accordion is fully open.
        await self.page.locator("#type").select_option(data["conn_type"])
        await self.page.get_by_label("Snowflake Account").fill(
            data["warehouse_account"]
        )
        await self.page.get_by_label("Warehouse").fill(data["warehouse"])
        await self.page.get_by_label("Database").fill(data["database"])
        await self.page.get_by_label("Role").fill(data["role"])
        await self.page.get_by_label("Schema").fill(data["schema"])
        await self.page.locator("#user").fill(data["user"])
        await self.page.get_by_label("Password").fill(data["password"])
        await self.screenshot(full_page=True)

        btn_next = self.page.get_by_role("button", name="Next")
        await btn_next.wait_for(state="attached")
        await btn_next.evaluate("el => el.click()")

        await self.page.locator("p", has_text="Testing connection...").wait_for(
            state="attached"
        )
        await self.screenshot(full_page=True)
        await self.page.get_by_text(
            "Connection to the Data Warehouse was successful"
        ).wait_for(state="attached")
        print("Step three completed")
