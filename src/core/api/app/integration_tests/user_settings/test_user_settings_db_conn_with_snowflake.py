import asyncio

import pytest
from integration_tests.base_test import PlaywrightChannelsTestCase, utils_test
from integration_tests.user_settings.base import git_ssh_key_test_connection
from playwright.async_api import expect

data = {
    "git_repo_ssh_url": "git@github.com:datacoves/balboa.git",
    "db_name": "test_db_name",
    "db_conn_template": "1",
    "db_auth_type": "key",
    "db_user": utils_test.secrets["snowflake_service_account"]["user"],
    "db_password": utils_test.secrets["snowflake_service_account"]["password"],
}


class UserSettingsDbConnectionWithSnowflakeTest(PlaywrightChannelsTestCase):
    def setUp(self):
        self._subpath = f"user_settings/{__name__}"
        return super().setUp()

    @pytest.mark.asyncio
    async def test_user_settings_db_connection_with_snowflake(self):
        """
        Test case user settings to create connection with Snowflake

        Steps:
            1. Generate SSH key to clone git repository.
            2. Auto-generate SSH key to database connection.
            3. Provide wrong SSH key to database connection.
            4. Testing database connection with credential username and password.
            5. Provide success SSH key to database connection.
            6. Testing test connection and edit buttons works.
            7. Go to workbench (transform tab) and check that git repo was cloned successfully
            8. Run dbt debug on terminal to validate db connection worked ok
        """

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
            await btn_open_user_menu.wait_for(state="attached")
            await btn_open_user_menu.click()
            await self.page.get_by_role("menuitem", name="Settings").click()
            await self.page.get_by_role("heading", name="Profile Settings").wait_for()
            await self.screenshot()

            # Testing
            await self.git_ssh_key_gen()
            await self.auto_generate_ssh_key()
            await self.delete_connection()
            await self.provide_error_ssh_key()
            await self.connection_with_data_success()
            await self.delete_connection(delete_ssh_key=False)
            await self.provide_success_ssh_key()
            await self.btn_connection_test()
            await self.btn_edit_test()
            await self.go_to_transform_tab()

            print("Testing user settings database connection completed")

        except Exception:
            await self.dump_pod_logs([("code-server", "code-server"), ("pomerium",)])
            raise

        finally:
            await self.asyncTearDown()

    async def git_ssh_key_gen(self):
        """Test generate ssh key to clone git repository"""
        await asyncio.sleep(1)
        tab_git_ssh_keys = self.page.get_by_role("tab", name="Git SSH Keys")
        await tab_git_ssh_keys.wait_for(state="visible")
        await tab_git_ssh_keys.wait_for(state="attached")
        await tab_git_ssh_keys.evaluate("el => el.click()")
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
        await self.clean_toast()

    async def auto_generate_ssh_key(self):
        """Autogenerate SSH key to testing connection"""
        tab_database_auth_keys = self.page.get_by_role("tab", name="Database Auth Keys")
        await tab_database_auth_keys.wait_for(state="visible")
        await tab_database_auth_keys.wait_for(state="attached")
        await tab_database_auth_keys.evaluate("el => el.click()")
        await self.page.locator("section").filter(
            has_text="Database authorization keysAdd this authorization key"
        ).get_by_role("button", name="Add").click()
        await self.page.get_by_role("menuitem", name="Auto-generate key pairs").click()
        await self.page.get_by_text("Key pairs successfully created").wait_for(
            state="attached"
        )
        await self.clean_toast()
        await self.screenshot(full_page=True)
        await self.connection_with_ssh_key_success()
        await self.screenshot(full_page=True)

    async def connection_with_ssh_key_success(self):
        """Makes the testing connection with the SSH key and validate the success message"""
        await self.page.get_by_role("tab", name="Database Connections").click()
        await self.page.locator("section").filter(
            has_text="Database connectionsConfigure Database connections for each project environment."
        ).get_by_role("button", name="Add").click()
        conn_section = self.page.locator("section").filter(
            has_text="New connection for"
        )
        await conn_section.locator("input").fill(data["db_name"])
        await conn_section.get_by_role(
            "combobox", name="Connection Template"
        ).select_option(index=1)
        await conn_section.get_by_role("combobox", name="Auth type").select_option(
            data["db_auth_type"]
        )
        await self.screenshot()
        await conn_section.get_by_role("combobox", name="Public key").select_option(
            index=1
        )
        await self.screenshot()
        await self.page.get_by_role("button", name="Save").click()
        await self.screenshot()
        await self.page.get_by_text(
            "Connection to the Data Warehouse was successful"
        ).wait_for(state="attached")
        await self.screenshot()
        await expect(
            self.page.get_by_role("row", name=f"{data['db_name']} snowflake")
        ).to_be_visible()
        await self.screenshot()

    async def delete_connection(self, delete_ssh_key=True):
        """Delete database connection"""
        database_conn = self.page.get_by_role("tab", name="Database Connections")
        await database_conn.wait_for(state="visible")
        await database_conn.wait_for(state="attached")
        await database_conn.evaluate("el => el.click()")
        tested_msg = self.page.get_by_role("row", name=f"{data['db_name']} snowflake")
        await tested_msg.wait_for(state="attached")
        await tested_msg.get_by_role("button").nth(2).click()
        delete_btn = self.page.get_by_role("button", name="Delete")
        await delete_btn.wait_for(state="attached")
        await delete_btn.click()

        if delete_ssh_key:
            # Delete private key
            await self.page.get_by_role("tab", name="Database Auth Keys").click()
            await self.page.locator("section").filter(
                has_text="Database authorization keysAdd this authorization key to your database account"
            ).get_by_role("button", name="Delete key").click()
            delete_btn = self.page.get_by_role("button", name="Delete")
            await delete_btn.wait_for(state="attached")
            await delete_btn.click()

    async def provide_error_ssh_key(self):
        """Testing connection with SSH key wrong and validate the error message"""
        await self.page.get_by_role("tab", name="Database Auth Keys").click()
        await self.page.locator("section").filter(
            has_text="Database authorization keysAdd this authorization key"
        ).get_by_role("button", name="Add").click()
        await self.page.get_by_role("menuitem", name="Provide private key").click()
        await self.page.get_by_label("Private key*").fill("ssh key dummy")
        await self.page.get_by_role("button", name="Save").click()
        await self.page.get_by_text("Error Creating key pairs").wait_for(
            state="attached"
        )
        await self.screenshot(full_page=True)
        await self.page.get_by_role("button", name="Cancel").click()

    async def connection_with_data_success(self):
        """Testing connection with success data and validate the success message"""
        await self.page.get_by_role("tab", name="Database Connections").click()
        await self.page.locator("section").filter(
            has_text="Database connectionsConfigure Database connections for each project environment."
        ).get_by_role("button", name="Add").click()
        conn_section = self.page.locator("section").filter(
            has_text="New connection for"
        )
        await conn_section.locator("input").fill(data["db_name"])
        await self.page.get_by_role(
            "combobox", name="Connection Template"
        ).select_option(index=1)
        # page.get_by_role("combobox", name="Auth type").select_option(index=0)  # Password
        await self.page.get_by_role("combobox", name="Auth type").press("Tab")
        await self.page.locator("#password").fill(data["db_password"])
        await self.page.get_by_role("button", name="Save").click()
        await self.page.get_by_text("Testing connection...").wait_for(
            state="attached",
        )
        await self.screenshot(full_page=True)
        await self.page.get_by_text(
            "Connection to the Data Warehouse was successful"
        ).wait_for(state="attached")
        await expect(
            self.page.get_by_role("row", name=f"{data['db_name']} snowflake")
        ).to_be_visible()
        await self.screenshot(full_page=True)

    async def provide_success_ssh_key(self):
        """Provide SSH key to testing connection"""
        await self.page.get_by_role("tab", name="Database Auth Keys").click()
        await self.page.locator("section").filter(
            has_text="Database authorization keysAdd this authorization key"
        ).get_by_role("button", name="Add").click()
        await self.page.get_by_role("menuitem", name="Provide private key").click()
        private_key = await utils_test.gen_private_key()
        await self.page.get_by_label("Private key*").fill(private_key)
        await self.page.get_by_role("button", name="Save").click()
        await self.page.get_by_text("Key pairs successfully created").wait_for(
            state="attached"
        )
        await self.clean_toast()
        await self.screenshot(full_page=True)
        await self.connection_with_ssh_key_success()
        await self.screenshot(full_page=True)

    async def btn_connection_test(self):
        """Testing that test connection button test works"""
        await self.page.get_by_role("tab", name="Database Connections").click()
        await self.page.get_by_role(
            "row", name=f"{data['db_name']} snowflake"
        ).get_by_role("button").first.click()
        await expect(
            self.page.get_by_text("Connection to the Data Warehouse was successful")
        ).to_be_visible(timeout=self.get_timeout(minutes=1))
        await self.clean_toast()

    async def btn_edit_test(self):
        """Testing that edit connection button works"""
        await self.page.get_by_role("tab", name="Database Connections").click()
        await self.page.get_by_role(
            "row", name=f"{data['db_name']} snowflake"
        ).get_by_role("button").nth(1).click()
        await expect(
            self.page.get_by_text("Edit connection for Analytics Development")
        ).to_be_visible()
        await self.page.get_by_role("button", name="Cancel").click()

    async def go_to_transform_tab(self):
        await asyncio.sleep(300)
        await self.page.goto("https://datacoveslocal.com/launchpad")
        btn_open_env = self.page.get_by_role("button", name="Open", exact=True)
        await btn_open_env.wait_for(
            state="attached", timeout=self.get_timeout(minutes=5)
        )
        await self.screenshot()
        await btn_open_env.click()

        await self.page.frame_locator('iframe[name="docs"]').get_by_role(
            "heading", name="Welcome to the Datacoves Documentation"
        ).wait_for(state="attached", timeout=self.get_timeout(minutes=5))

        await self.screenshot()

        # Open VS Code
        await self.page.get_by_text("Transform").click()
        transform_iframe = self.page.frame_locator('iframe[name="transform"]')
        await transform_iframe.get_by_role("treeitem", name=".gitignore").wait_for(
            state="attached", timeout=self.get_timeout(minutes=7)
        )
        side_bar_explorer = transform_iframe.get_by_role(
            "heading", name="Explorer", exact=True
        )
        await side_bar_explorer.wait_for(state="attached")
        await side_bar_explorer.click()
        await self.screenshot()

        terminal = transform_iframe.locator(".terminal-widget-container")
        await terminal.wait_for(state="attached", timeout=self.get_timeout(minutes=1))
        await terminal.click()

        terminal_input = transform_iframe.get_by_role("textbox", name="Terminal")
        await terminal_input.wait_for(
            state="attached", timeout=self.get_timeout(minutes=1)
        )
        await terminal_input.fill("dbt debug")
        await terminal_input.press("Enter")

        await asyncio.sleep(60)
        await self.screenshot()

        output_cmd = await transform_iframe.locator("div.xterm-rows").inner_text()
        print("dbt debug:", output_cmd)
        # FIXME DCV-2022: dbt-debug's 'all checks passed' output differs between local and github runs
        assert ("All checks passed" in output_cmd) or ("Allcheckspassed" in output_cmd)
