import asyncio
import gc
import os
import shutil
import traceback
from itertools import count
from pathlib import Path
from typing import List, Tuple
from uuid import uuid4

from billing.models import Plan
from channels.db import database_sync_to_async
from channels.testing import ChannelsLiveServerTestCase
from clusters import workspace
from clusters.config_loader.cluster import ClusterConfigLoader
from clusters.config_loader.environment import EnvironmentConfigLoader
from clusters.models import Cluster
from codegen.models import SQLHook, Template
from daphne.server import Server
from daphne.testing import DaphneProcess, _reinstall_reactor
from django.db import connection
from integration_tests import utils_test
from playwright.async_api import ConsoleMessage, Page, async_playwright
from projects.management.commands.load_releases import load_releases
from projects.models import (
    ConnectionTemplate,
    ConnectionType,
    Environment,
    Profile,
    Project,
    Release,
)
from twisted.internet import reactor
from users.models import Group, User

RECORD_VIDEO = False


class DaphneProcessDatacoves(DaphneProcess):
    def __init__(self, host, get_application, kwargs=None, setup=None, teardown=None):
        super().__init__("0.0.0.0", get_application, kwargs, setup, teardown)

    def run(self):
        # OK, now we are in a forked child process, and want to use the reactor.
        # However, FreeBSD systems like MacOS do not fork the underlying Kqueue,
        # which asyncio (hence asyncioreactor) is built on.
        # Therefore, we should uninstall the broken reactor and install a new one.

        from daphne.endpoints import build_endpoint_description_strings

        _reinstall_reactor()

        application = self.get_application()

        try:
            # Create the server class
            endpoints = build_endpoint_description_strings(host=self.host, port=8000)
            self.server = Server(
                application=application,
                endpoints=endpoints,
                signal_handlers=False,
                **self.kwargs,
            )
            # Set up a poller to look for the port
            reactor.callLater(0.1, self.resolve_port)
            # Run with setup/teardown
            if self.setup is not None:
                self.setup()
            try:
                self.server.run()
            finally:
                if self.teardown is not None:
                    self.teardown()
                self._cleanup_reactor()

        except BaseException as e:
            # Put the error on our queue so the parent gets it
            self.errors.put((e, traceback.format_exc()))

    def _cleanup_reactor(self):
        try:
            # Forzar la limpieza del reactor
            if reactor.running:
                reactor.stop()
            for delayed in reactor.getDelayedCalls():
                if delayed.active():
                    delayed.cancel()
        except Exception:
            pass


class ChannelsLiveServerTestCaseDatacoves(ChannelsLiveServerTestCase):
    ProtocolServerProcess = DaphneProcessDatacoves

    @classmethod
    def tearDownClass(cls):
        try:
            # Force cleanup of server processes
            if hasattr(cls, "server_thread") and cls.server_thread is not None:
                cls.server_thread.terminate()
                cls.server_thread.join(timeout=1)
        except Exception:
            pass
        super().tearDownClass()


class PlaywrightChannelsTestCase(ChannelsLiveServerTestCaseDatacoves):
    DEFAULT_TEST_DELAY = 2.0

    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self._domain = "datacoveslocal.com"
        self._ssh_key_title: str = None
        self._subpath = None
        self._screenshot_cont = count(1)
        self._page: Page = None
        self._browser_console = []
        self._context = None
        self._browser = None
        self._playwright = None
        self.test_delay = float(os.getenv("TEST_DELAY", self.DEFAULT_TEST_DELAY))

    async def asyncSetUp(self):
        """Async setup method to initialize browser context"""
        await self._wait_between_tests()
        await self._ensure_clean_browser_state()
        await self.set_browser_context()

    async def _wait_between_tests(self):
        """Wait between tests with the configured time"""
        delay = getattr(self, "test_delay", self.DEFAULT_TEST_DELAY)
        await asyncio.sleep(delay)

    async def _ensure_clean_browser_state(self):
        """Ensure the browser state is clean before starting"""
        await self.teardown_browser()
        gc.collect()
        await asyncio.sleep(0.5)

    async def asyncTearDown(self):
        """Async teardown method to clean up browser resources"""
        if self._page and RECORD_VIDEO:
            await self.save_video()

        await self.teardown_browser()
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

        gc.collect()
        await asyncio.sleep(0.5)

    def tearDown(self):
        """Synchronous teardown for database cleanup"""
        try:
            envs_deleted, details = Environment.objects.all().delete()
            print(f"Environments deleted: {envs_deleted}")
            print(f"Details: {details}")

            if self._ssh_key_title:
                utils_test.github_ssh_delete_all_by_title(self._ssh_key_title)

            """
            Workaround to fix:
            psycopg2.errors.FeatureNotSupported: cannot truncate a table referenced in a foreign key constraint
            DETAIL:  Table "knox_authtoken" references "users_user".
            HINT:  Truncate table "knox_authtoken" at the same time, or use TRUNCATE ... CASCADE.
            """
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DO $$
                    DECLARE constraint_name TEXT;
                    BEGIN
                        SELECT conname INTO constraint_name
                        FROM pg_constraint
                        WHERE conrelid = 'knox_authtoken'::regclass
                        AND contype = 'f';

                        IF constraint_name IS NOT NULL THEN  -- Check if the constraint exists
                            EXECUTE format('ALTER TABLE knox_authtoken DROP CONSTRAINT %I', constraint_name);
                        END IF;
                    END $$;
                """
                )

        finally:
            super().tearDown()

    async def teardown_browser(self):
        """Clean up browser resources"""
        try:
            if self._context:
                await self._context.close()
                print("Context closed.")
            if self._browser:
                await self._browser.close()
                print("Browser closed.")
            if self._playwright:
                await self._playwright.stop()
                print("Playwright stopped.")
        except Exception as e:
            print(f"Error during browser teardown: {e}")

    async def set_browser_context(self):
        """Initialize browser context with proper configuration"""
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.firefox.launch(
                headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
            )

            video_config = (
                {
                    "record_video_dir": f"integration_tests/output/{self._subpath}/video",
                    "record_video_size": {"width": 1280, "height": 720},
                }
                if RECORD_VIDEO
                else {}
            )

            self._context = await self._browser.new_context(
                ignore_https_errors=True,
                viewport={"width": 1280, "height": 720},
                **video_config,
            )

            self._page = await self._context.new_page()
            self._page.set_default_timeout(utils_test.DEFAULT_TIMEOUT)
            self._page.on(
                "console",
                lambda msg: asyncio.create_task(self.handle_console_message(msg)),
            )
        except Exception as e:
            print(f"Error during browser setup: {e}")
            await self.teardown_browser()
            raise

    async def save_video(self):
        """Save recorded video if enabled"""
        try:
            if hasattr(self._page, "video") and self._page.video:
                video_path = await self._page.video.path()
                new_path = f"integration_tests/output/{self._subpath}/video.webm"
                shutil.move(video_path, new_path)
        except Exception as e:
            print(f"Error saving video: {e}")

    @property
    def page(self) -> Page:
        return self._page

    @property
    def domain(self) -> str:
        return self._domain

    @property
    def get_release(self) -> str:
        """Get release number from cluster-params.yaml"""
        return os.getenv("RELEASE")

    @property
    def ssh_key_title(self) -> str:
        if self._ssh_key_title is None:
            self._ssh_key_title = str(uuid4())
        return self._ssh_key_title

    def get_timeout(self, minutes) -> int:
        return minutes * utils_test.ONE_MINUTE_IN_MS

    async def handle_console_message(self, msg: ConsoleMessage):
        if "JSHandle@object" in msg.text:
            args_values = [await arg.evaluate("arg => arg") for arg in msg.args]
            text = " ".join(map(str, args_values))
        else:
            text = msg.text

        self._browser_console.append(f"[{msg.type}] {text}")

    async def dump_browser_console(self):
        dump_path = Path(f"integration_tests/output/{self._subpath}/logs/")
        dump_path.mkdir(parents=True, exist_ok=True)
        filename = "browser_console.txt"
        dump_path = dump_path / filename

        with open(dump_path, "w") as f:
            f.writelines(
                [
                    line if line.endswith("\n") else line + "\n"
                    for line in self._browser_console
                ]
            )

    async def dump_pod_logs(self, pods: List[Tuple[str, str]] = []):
        await self.screenshot()
        await self.dump_browser_console()
        await utils_test.dump_pod_status(self._subpath)
        for pod in pods:
            pod_name = pod[0]
            container_name = pod[1] if len(pod) == 2 else None
            await utils_test.dump_pod_logs(
                self._subpath, pod_name=pod_name, container=container_name
            )

        if RECORD_VIDEO:
            # Close the context before getting the video
            await self._context.close()
            await self.save_video()

    async def screenshot(self, delay=1, full_page=False) -> str:
        """Gets screenshots path to storage screenshots"""
        await asyncio.sleep(delay)
        sufix = next(self._screenshot_cont)
        path = f"integration_tests/output/{self._subpath}/screenshots/screenshot_{sufix}.png"
        await self._page.screenshot(path=path, full_page=full_page)

    async def clean_toast(self):
        await self._page.get_by_role("button", name="Close").first.click()

    async def user_session(self):
        password = "testing123"

        @database_sync_to_async
        def create_user():
            user = User.objects.create_user(
                email="john@datacoves.com",
                password=password,
                name="John",
                setup_enabled=True,
            )
            user.is_superuser = True
            user.save()
            return user

        user = await create_user()
        print("User created:", user.email)
        self.user_session = {"user": user, "password": password}
        return self.user_session

    async def cluster_setup(self, user):
        @database_sync_to_async
        def create_cluster():
            utils_test.check_namespace_terminated()

            load_releases()
            cluster_params = {
                "domain": self._domain,
                "context": "kind-datacoves-cluster",
                "provider": "kind",
                "kubernetes_version": "1.35.0",
                "release": self.get_release,
                "account": {
                    "name": "Local",
                    "slug": "local",
                    "owner": {"email": "hey@datacoves.com", "name": "Datacoves Admin"},
                },
                "projects": {
                    "analytics": {
                        "name": "Analytics",
                        "slug": "analytics-local",
                        "clone_strategy": "http_clone",
                        "repository": {
                            "url": "https://github.com/datacoves/balboa.git",
                            "git_url": "git@github.com:datacoves/balboa.git",
                        },
                        "groups": {
                            "admins": ["ADMIN-TEST"],
                            "developers": ["DEVELOPER-TEST"],
                            "viewers": ["VIEWER-TEST"],
                        },
                    }
                },
                "features_enabled": {
                    "admin_users": True,
                    "admin_groups": True,
                    "admin_account": True,
                    "admin_billing": True,
                    "admin_projects": True,
                    "accounts_signup": False,
                    "admin_invitations": True,
                    "admin_environments": True,
                    "admin_connections": True,
                    "admin_integrations": True,
                    "admin_secrets": True,
                    "admin_service_credentials": True,
                    "user_profile_change_name": True,
                    "user_profile_delete_account": True,
                    "user_profile_change_credentials": True,
                    "user_profile_change_ssh_keys": True,
                    "user_profile_change_ssl_keys": True,
                    "codeserver_restart": True,
                },
            }

            cluster = ClusterConfigLoader.load(params=cluster_params)

            env_config = {
                "name": "Development",
                "project": "analytics-local",
                "type": "dev",
                "release": self.get_release,
                "services": {
                    "airbyte": {"enabled": False},
                    "airflow": {"enabled": False},
                    "code-server": {"enabled": True},
                    "dbt-docs": {"enabled": False},
                    "superset": {"enabled": False},
                },
                "dbt_home_path": "transform",
                "dbt_profiles_dir": "automate",
            }

            env = EnvironmentConfigLoader.load(
                env_slug=utils_test.ENVIRONMENT_NAME,
                env_config=env_config,
                run_async=False,
            )

            airflow_config = {
                "settings": {
                    "webserver_master_timeout": 300,
                },
                "override_values": {
                    "webserver": {
                        "livenessProbe": {
                            "initialDelaySeconds": 300,
                            "periodSeconds": 10,
                            "timeoutSeconds": 30,
                            "failureThreshold": 30,
                        },
                        "startupProbe": {
                            "failureThreshold": 30,
                            "periodSeconds": 10,
                            "timeoutSeconds": 20,
                        },
                    },
                },
            }

            env.airflow_config.update(airflow_config)
            Environment.objects.filter(id=env.id).update(
                airflow_config=env.airflow_config
            )

            user.groups.set(Group.objects.all())
            workspace.sync(env, "register_environment.handle", False)

            conn_type = ConnectionType.objects.filter(name="Snowflake").first()
            print("Conn type created:", conn_type)

            template = Template.objects.create(
                name="Generate test username",
                slug="generate_test_username",
                description="Username literal",
                content="svc_datacoves_platform_ci",
                context_type=Template.CONTEXT_TYPE_NONE,
                format=Template.FORMAT_NONE,
                enabled_for=["ConnectionTemplate"],
            )
            print("Template created:", template)

            conn_template = ConnectionTemplate.objects.create(
                name="main",
                connection_user=ConnectionTemplate.CONNECTION_USER_FROM_TEMPLATE,
                project=Project.objects.first(),
                type=conn_type,
                connection_user_template=template,
                connection_details={
                    "account": "toa80779",
                    "warehouse": "wh_integration",
                    "database": "balboa_dev",
                    "role": "bot_integration",
                    "mfa_protected": False,
                },
            )
            print("Conn template created:", conn_template)

            sql_hook = SQLHook.objects.get(slug="set_snowflake_user_public_key")
            sql_hook.connection_overrides = {
                "role": "SECURITYADMIN",
                "user": utils_test.secrets["snowflake_service_account"][
                    "template_db_user"
                ],
                "password": utils_test.secrets["snowflake_service_account"][
                    "template_db_password"
                ],
            }
            sql_hook.enabled = True
            sql_hook.save()
            print("SQLHook updated:", sql_hook)

            return cluster

        cluster = await create_cluster()
        return cluster

    async def cluster_setup_wizard(self):
        @database_sync_to_async
        def create_cluster():
            load_releases()

            connections_types = [
                ("Snowflake", "snowflake"),
                ("Redshift", "redshift"),
                ("Bigquery", "bigquery"),
                ("Databricks", "databricks"),
            ]
            for name, slug in connections_types:
                conn_type = ConnectionType.objects.create(name=name, slug=slug)
                print("Created connecion type:", conn_type)

            profile = Profile.objects.create(name="dbt", slug="default")
            print("Created profile:", profile)

            plan = Plan.objects.create(
                name="Starter - Monthly",
                slug="starter-monthly",
                billing_period="monthly",
                trial_period_days=14,
                kind="starter",
            )
            print("Created plan:", plan)

            release = Release.objects.order_by("-released_at").first()
            cluster = Cluster.objects.create(domain=self._domain, release=release)
            cluster.features_enabled["accounts_signup"] = True
            cluster.limits = {
                "max_cluster_active_accounts": 20,
                "max_cluster_active_trial_accounts": 10,
            }
            cluster.code_server_config = {
                "overprovisioning": {"enabled": False, "replicas": "1"},
                "max_code_server_pods_per_node": 16,
                "resources": {
                    "requests": {"memory": "250Mi", "cpu": "100m"},
                    "limits": {"memory": "2Gi", "cpu": "1"},
                },
            }
            cluster.save()
            print("Created cluster:", cluster)
            return cluster

        cluster = await create_cluster()
        return cluster
