import re

from integration_tests.utils_test import ONE_MINUTE_IN_MS, github_ssh_key_create
from playwright.async_api import Page, expect


async def git_ssh_key_test_connection(
    page: Page, git_repo_ssh_url: str, is_success: bool, ssh_key_title: str
) -> int:
    ssh_input = page.get_by_text(re.compile("^ssh-ed25519", re.IGNORECASE))
    ssh = await ssh_input.input_value()
    await expect(ssh_input).to_contain_text("ssh-ed25519")

    await github_ssh_key_create(title=ssh_key_title, ssh_key=ssh)

    await page.get_by_role("row", name=f"{git_repo_ssh_url}").get_by_role(
        "button"
    ).evaluate("el => el.click()")

    if is_success:
        await expect(page.get_by_role("button", name="Re-test")).to_be_visible(
            timeout=ONE_MINUTE_IN_MS
        )
    else:
        await expect(page.get_by_text("Error accessing Git Repository")).to_be_visible(
            timeout=ONE_MINUTE_IN_MS
        )
