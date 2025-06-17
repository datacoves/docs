import pytest
from integration_tests.base_test import PlaywrightChannelsTestCase, utils_test
from integration_tests.user_settings.base import git_ssh_key_test_connection
from playwright.async_api import expect

data = {"git_repo_ssh_url": "git@github.com:datacoves/balboa.git"}


class UserSettingsGitConnectionTest(PlaywrightChannelsTestCase):
    def setUp(self):
        self._subpath = f"user_settings/{__name__}"
        return super().setUp()

    @pytest.mark.asyncio
    async def test_user_settings_git_connection(self):
        try:
            await self.asyncSetUp()

            user_session = await self.user_session()
            user = user_session["user"]
            cluster = await self.cluster_setup(user=user)

            # Login
            await utils_test.login(
                page=self.page,
                username=user.email,
                password=user_session["password"],
                domain=cluster.domain,
            )

            # Go to Launchpad
            await self.page.goto("https://datacoveslocal.com/launchpad")
            header_launchpad = self.page.get_by_role("heading", name="Launch Pad")
            await header_launchpad.wait_for(timeout=self.get_timeout(minutes=1))
            btn_open_env = self.page.get_by_role("button", name="Open", exact=True)
            await btn_open_env.wait_for(
                state="attached", timeout=self.get_timeout(minutes=5)
            )
            await self.screenshot()

            # Go to Profile Settings
            btn_open_user_menu = self.page.get_by_role("button", name="Open user menu")
            await btn_open_user_menu.wait_for(
                state="attached", timeout=self.get_timeout(minutes=5)
            )
            await btn_open_user_menu.click()
            menu_user_settings = self.page.get_by_role("menuitem", name="Settings")
            await menu_user_settings.is_visible()
            await menu_user_settings.click()
            header_user_settings = self.page.get_by_role(
                "heading", name="Profile Settings"
            )
            await header_user_settings.wait_for()
            await self.screenshot()

            # Tests with user SSH Keys
            await self.when_provide_git_ssh_key_success()
            await self.when_provide_git_ssh_key_wrong()
            await self.when_git_ssh_key_is_auto_generate()
            print("Testing user settings git completed")

        except Exception:
            await self.dump_pod_logs([("code-server", "code-server"), ("pomerium",)])
            raise

        finally:
            await self.asyncTearDown()

    async def when_provide_git_ssh_key_success(self):
        """Testing git connection with SSH key provide and success message"""
        await self.page.get_by_role("tab", name="Git SSH Keys").click()
        btn_add = (
            self.page.locator("section")
            .filter(
                has_text="Git SSH keysAdd this SSH key to your git server account to clone your repos."
            )
            .get_by_role("button", name="Add")
        )
        await btn_add.click()
        await self.page.get_by_role("menuitem", name="Provide private key").click()
        ssh_key = await utils_test.gen_open_ssh_key()
        await self.page.get_by_label("Private key*").fill(ssh_key)
        await self.screenshot()
        await self.page.get_by_role("button", name="Save").click()
        await self.page.get_by_text("SSH key pairs successfully created").wait_for(
            state="attached"
        )
        await self.clean_toast()
        await git_ssh_key_test_connection(
            page=self.page,
            git_repo_ssh_url=data["git_repo_ssh_url"],
            is_success=True,
            ssh_key_title=self.ssh_key_title,
        )
        await self.screenshot()
        await self.clean_toast()

        # Delete ssh key
        await self.page.get_by_role("button", name="Delete key").click()
        delete_btn = self.page.get_by_role("button", name="Delete")
        await delete_btn.wait_for(state="attached")
        await delete_btn.click()
        await self.page.get_by_text("SSH Key successfully deleted.").wait_for(
            state="attached"
        )
        await self.screenshot()
        await self.clean_toast()

    async def when_provide_git_ssh_key_wrong(self):
        """Testing git connection with SSH key provide with extra lines and malformat"""

        await self.page.get_by_role("tab", name="Git SSH Keys").click()
        btn_add = (
            self.page.locator("section")
            .filter(
                has_text="Git SSH keysAdd this SSH key to your git server account to clone your repos."
            )
            .get_by_role("button", name="Add")
        )
        btn_provide_ssh = self.page.get_by_role("menuitem", name="Provide private key")
        private_key_input = self.page.get_by_label("Private key*")

        # SSH Key provided has new lines
        await btn_add.click()
        await btn_provide_ssh.click()
        ssh_key = await utils_test.gen_open_ssh_key()
        await private_key_input.fill(f"\n\n{ssh_key}\n")
        await self.screenshot()
        await self.page.get_by_role("button", name="Save").click()
        await self.page.get_by_text("SSH key pairs successfully created").wait_for(
            state="attached"
        )
        await self.screenshot()
        await self.clean_toast()

        await git_ssh_key_test_connection(
            page=self.page,
            git_repo_ssh_url=data["git_repo_ssh_url"],
            is_success=False,
            ssh_key_title=self.ssh_key_title,
        )
        await self.screenshot()
        await self.clean_toast()

        await self.page.get_by_role("button", name="Delete key").click()
        delete_btn = self.page.get_by_role("button", name="Delete")
        await delete_btn.wait_for(state="attached")
        await delete_btn.click()
        await self.page.get_by_text("SSH Key successfully deleted.").wait_for(
            state="attached"
        )
        await self.screenshot()

        # SSH Key provided is wrong
        await btn_add.click()
        await btn_provide_ssh.click()
        await private_key_input.fill("ssh test dummy wrong")
        await self.page.get_by_role("button", name="Save").click()
        await self.page.get_by_text("Error Creating SSH key pairs").wait_for(
            state="attached"
        )
        await self.screenshot()
        await self.page.get_by_role("button", name="Cancel").click()
        await self.clean_toast()

    async def when_git_ssh_key_is_auto_generate(self):
        """Testing git connection with SSH key auto-generated and success message"""

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
        await self.screenshot()
