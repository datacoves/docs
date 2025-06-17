import asyncio
import base64

import pytest
from integration_tests.base_test import utils_test
from integration_tests.setup_wizard.base import SetupWizardBase

data = {
    "account_name": "Acme Inc.",
    "first_project": "Commercial Analytics",
    "conn_type": "bigquery",
    "dataset": "default",
    "key_file": base64.b64decode(
        utils_test.secrets["bigquery_service_account"]["Key_file_base64"]
    ).decode("utf-8"),
    "git_repo_ssh_url": "git@github.com:datacoves/balboa.git",
    "release_branch": "main",
}


class SetupWizardWithBigqueryTest(SetupWizardBase):
    def setUp(self):
        self._subpath = f"setup_wizard/{__name__}"
        return super().setUp()

    @pytest.mark.asyncio
    async def test_setup_wizard_with_bigquery(self):
        """Test to setup an account with Bigquery"""

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
            print("Setup wizard completed with Bigquery completed")

        except Exception:
            await self.dump_pod_logs()
            raise

        finally:
            await self.asyncTearDown()

    async def setup_wizard_step_three(self):
        """Complete the step three with Bigquery warehouse"""

        await asyncio.sleep(2)  # Wait until the accordion is fully open.
        await self.page.locator("#type").select_option(data["conn_type"])
        await self.page.get_by_label("Dataset").fill(data["dataset"])
        await self.page.get_by_label("Keyfile content").fill(data["key_file"])
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
