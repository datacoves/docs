import pytest
from integration_tests.workbench.base import WorkbenchBase, WorkbenchServicesEnum
from playwright.async_api import expect


class WorkbenchAirflowTest(WorkbenchBase):
    def setUp(self):
        self._subpath = f"workbench/{__name__}"
        return super().setUp()

    @pytest.mark.asyncio
    async def test_workbench_airflow(self):
        """
        Test that enables the Airflow stack service on Environment page
        and ensures Airflow is available and accessible on the Workbench

        Steps:
            1. Login
            2. Go to Launchpad
            3. Go to Projects admin and enable Project by creating a SSH Key and testing it
            4. Go to Environments admin and toggle Airflow stack service
            5. Go to Launchpad and Workbench
            6. Go to Airflow and 'sign in with Datacoves'
            7. Assert Airflow landing content is present
        """

        try:
            await self.asyncSetUp()

            user_session = await self.user_session()
            user = user_session["user"]
            await self.cluster_setup(user=user)

            await self.go_to_launchpad(user.email, user_session["password"])
            await self.enable_project()
            await self.enable_environment_service(
                service=WorkbenchServicesEnum.AIRFLOW, needs_extra_config=True
            )
            await self.configure_airflow_stack()
            await self.go_to_orchestrate_tab()
            print("Workbench Airflow completed")

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

    async def configure_airflow_stack(self):
        await self.page.get_by_role("tab", name="Airflow settings").click()
        await self.page.locator('[id="airflow_config\\.dags_source"]').select_option(
            "git"
        )
        await self.page.get_by_label("Git branch name").fill("main")
        await self.screenshot(full_page=True)
        await self.page.get_by_role("button", name="Save Changes").click()
        await self.page.get_by_role(
            "row", name="Analytics Development 0 service connections"
        ).wait_for(state="attached")
        await self.screenshot()

    async def go_to_orchestrate_tab(self):
        await self.get_into_workbench(service=WorkbenchServicesEnum.AIRFLOW)
        await self.page.goto(f"https://airflow-tst001.{self.domain}")
        await self.screenshot()
        await self.page.get_by_text("Sign In with datacoves").click()
        await self.screenshot(delay=5)
        await expect(self.page.get_by_role("heading", name="DAGs")).to_be_visible()
