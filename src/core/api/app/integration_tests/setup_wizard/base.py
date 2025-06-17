import asyncio

from integration_tests.base_test import PlaywrightChannelsTestCase, utils_test
from playwright.async_api import expect


class SetupWizardBase(PlaywrightChannelsTestCase):
    async def lauchpad_create_new_account(self):
        """Select to create a new account"""

        await self.page.goto(f"http://{self.domain}/launchpad")
        await self.page.locator(".chakra-container").wait_for(state="attached")
        await self.screenshot(full_page=True)
        await expect(self.page).to_have_title("Datacoves")
        await expect(
            self.page.get_by_role("heading", name="Welcome to Datacoves!")
        ).to_be_visible()

        await self.page.get_by_role("button", name="Continue account setup").evaluate(
            "el => el.click()"
        )
        await expect(
            self.page.get_by_role("heading", name="Account Setup")
        ).to_be_visible()
        await self.screenshot(full_page=True)

    async def setup_wizard_step_one(self, data: dict):
        """Complete the step one"""

        await asyncio.sleep(2)  # Wait until the accordion is fully open.
        account_name_control = self.page.get_by_label("Account name")
        await account_name_control.is_visible()
        await account_name_control.fill(data["account_name"])
        btn_next = self.page.get_by_role("button", name="Next")
        await btn_next.wait_for(state="attached")
        await self.screenshot(full_page=True)
        await btn_next.evaluate("el => el.click()")
        print("Step one completed")

    async def setup_wizard_step_two(self, data: dict):
        """Complete the step two only with default option"""
        await asyncio.sleep(2)  # Wait until the accordion is fully open.
        project_control = self.page.get_by_label("First Project")
        await project_control.is_visible()
        await project_control.fill(data["first_project"])
        await asyncio.sleep(2)
        extract_and_load_data_control = self.page.locator(
            "span", has_text="Extract and Load data"
        )
        await extract_and_load_data_control.wait_for(state="visible")
        await extract_and_load_data_control.wait_for(state="attached")
        await extract_and_load_data_control.evaluate("el => el.click()")
        await self.page.locator("span", has_text="Orchestrate").evaluate(
            "el => el.click()"
        )
        await self.page.locator("span", has_text="Analyze").evaluate("el => el.click()")
        btn_next = self.page.get_by_role("button", name="Next")
        await btn_next.wait_for(state="attached")
        await self.screenshot(full_page=True)
        await btn_next.evaluate("el => el.click()")
        print("Step two completed")

    async def setup_wizard_step_four(self, data: dict):
        """Complete step four to Github reposotory upload ssh keys"""

        await asyncio.sleep(2)  # Wait until the accordion is fully open.
        git_repo_control = self.page.get_by_label("Git Repo SSH URL")
        await git_repo_control.is_visible()
        await git_repo_control.fill(data["git_repo_ssh_url"])
        await self.page.get_by_label("Release Branch").fill(data["release_branch"])

        # Select Key type
        await self.page.get_by_role("combobox", name="SSH key type").select_option(
            "ed25519"
        )
        await self.screenshot(full_page=True)

        # SSH develop
        develop_ssh_input = self.page.get_by_label("SSH Development Key")
        develop_ssh = await develop_ssh_input.input_value()
        await expect(develop_ssh_input).to_contain_text("ssh")

        # SSH deploy
        deploy_ssh_input = self.page.get_by_label("SSH Deploy Key")
        deploy_ssh = await deploy_ssh_input.input_value()
        await expect(deploy_ssh_input).to_contain_text("ssh")
        await self.screenshot(full_page=True)

        btn_next = self.page.get_by_role("button", name="Next")
        await btn_next.wait_for(state="attached")
        await btn_next.evaluate("el => el.click()")

        await self.page.locator("p", has_text="Testing connection...").wait_for(
            state="attached"
        )
        await self.screenshot(full_page=True)

        # Test message error ssh keys not configurated
        msg_error = self.page.locator(
            "div", has_text="Error accessing Git Repository"
        ).first
        await msg_error.wait_for(state="attached")
        await expect(msg_error).to_contain_text("Error accessing Git Repository")
        await self.screenshot(full_page=True)

        await utils_test.github_ssh_key_create(self.ssh_key_title, develop_ssh)
        await utils_test.github_ssh_key_create(self.ssh_key_title, deploy_ssh)

        btn_next = self.page.get_by_role("button", name="Next")
        await btn_next.wait_for(state="attached")
        await btn_next.evaluate("el => el.click()")

        await self.page.locator("p", has_text="Testing connection...").wait_for(
            state="attached"
        )
        await self.screenshot(full_page=True)

        # Test message success configurated
        await self.page.get_by_text(
            "Connection to the Git Repository was successful."
        ).wait_for(state="attached", timeout=self.get_timeout(minutes=2))
        await self.screenshot(full_page=True)
        print("Step four completed")

    async def setup_wizard_step_five(self):
        """Complete step five about environment configuration"""

        await asyncio.sleep(2)  # Wait until the accordion is fully open.
        dbt_home_path_control = self.page.get_by_role("combobox", name="dbt home path")
        await dbt_home_path_control.is_visible()
        await dbt_home_path_control.select_option("transform")
        await self.page.locator('input[id="dbt_profile"][name="dbt_profile"]').fill(
            "default"
        )
        await self.page.get_by_role("button", name="Finish").evaluate(
            "el => el.click()"
        )
        await self.screenshot(full_page=True)
        print("Step five completed")

    async def setup_wizard_lauchpad(self, data: dict):
        """Test Launchpad"""

        launchpad = self.page.get_by_role("heading", name="Launch Pad")
        await launchpad.wait_for(timeout=self.get_timeout(minutes=1))
        await self.screenshot(full_page=True)

        """
        Expect:
        1. The name project
        2. Environment Development
        """
        await expect(launchpad).to_be_visible()
        await expect(
            self.page.get_by_role("heading", name=data["first_project"])
        ).to_be_visible()
        await expect(
            self.page.get_by_role("heading", name="Development")
        ).to_be_visible()
