import pytest
from integration_tests.workbench.base import WorkbenchBase, WorkbenchServicesEnum
from playwright.async_api import expect


class WorkbenchSupersetTest(WorkbenchBase):
    def setUp(self):
        self._subpath = f"workbench/{__name__}"
        return super().setUp()

    @pytest.mark.asyncio
    async def test_workbench_superset(self):
        """
        Test that enables the Superset stack service on Environment page
        and ensures Superset is available and accessible on the Workbench

        Steps:
            1. Login
            2. Go to Launchpad
            3. Go to Projects admin and enable Project by creating a SSH Key and testing it
            4. Go to Environments admin and toggle Superset stack service
            5. Go to Launchpad and Workbench
            6. Go to Superset and 'sign in with Datacoves'
            7. Assert Superset landing content is present
        """

        try:
            await self.asyncSetUp()

            user_session = await self.user_session()
            user = user_session["user"]
            await self.cluster_setup(user=user)

            await self.go_to_launchpad(user.email, user_session["password"])
            await self.enable_project()
            await self.enable_environment_service(
                service=WorkbenchServicesEnum.SUPERSET
            )
            await self.go_to_analyze_tab()
            print("Workbench Superset completed")

        except Exception:
            pods = [
                ("pomerium",),
                ("superset-init-db",),
                ("superset",),
            ]
            await self.dump_pod_logs(pods=pods)
            raise

        finally:
            await self.asyncTearDown()

    async def go_to_analyze_tab(self):
        await self.get_into_workbench(service=WorkbenchServicesEnum.SUPERSET)
        await self.page.goto(f"https://superset-tst001.{self.domain}")
        await self.screenshot()
        await self.page.get_by_text("Sign In with datacoves").click()
        await self.screenshot(delay=5)
        await expect(
            self.page.get_by_text("Other dashboards will appear here")
        ).to_be_visible(timeout=self.get_timeout(minutes=2))
