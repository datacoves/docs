import json
import logging
import uuid

from asgiref.sync import sync_to_async
from celery import group
from channels.generic.websocket import AsyncWebsocketConsumer
from clusters.builder import WorkbenchBuilder

from lib.utils import serialize_datetime

from .tasks import sync_user_workloads_status

logger = logging.getLogger(__name__)


class AccountConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = None
        self.user = self.scope["user"]
        self.account_slug = self.scope["url_route"]["kwargs"]["account_slug"]

        if self.user and self.user.is_authenticated and self.account_slug:
            group_name = f"workspace_user_account_slug_{self.account_slug}_user_slug_{self.user.slug}"
            self.group_name = group_name

            # Join group
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

        else:
            await self.close()

    async def disconnect(self, close_code):
        # Leave group
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        logger.debug("WEBSOCKET message received %s", text_data)

        message_type = text_data_json["message_type"]
        if message_type == "env.status":
            env_slugs = text_data_json["env_slugs"]
            component = text_data_json["component"]
            attempt = text_data_json.get("attempt", 1)
            await self.env_status_check(env_slugs.split(","), component, attempt)

        elif message_type == "env.restart.code-server":
            env_slug = text_data_json["env_slug"]
            await self.workbench_code_server_restart(env_slug)

        elif message_type == "env.start.local-airflow":
            env_slug = text_data_json["env_slug"]
            await self.workbench_start_local_airflow(env_slug)

        elif message_type == "env.heartbeat":
            env_slug = text_data_json["env_slug"]
            await self.workbench_heartbeat(env_slug)

        else:
            logger.warning("Unknown web socket message type %s", message_type)

    @sync_to_async
    def env_status_check(self, env_slugs: list, component: str, attempt: int):
        tasks = []
        for env_slug in env_slugs:
            uid = str(uuid.uuid4())
            task_id = f"env.state.{env_slug}.{self.user.slug}-{uid}"
            tasks.append(
                sync_user_workloads_status.s(
                    account_slug=self.account_slug,
                    env_slug=env_slug,
                    user_slug=self.user.slug,
                ).set(task_id=task_id)
            )

        if tasks:
            # Execute tasks in parallel
            group(tasks)(kwargs={"component": component, "attempt": attempt})

        return tasks

    @sync_to_async
    def workbench_heartbeat(self, env_slug):
        WorkbenchBuilder(user=self.user, env_slug=env_slug).heartbeat()

    @sync_to_async
    def workbench_code_server_restart(self, env_slug):
        WorkbenchBuilder(
            user=self.user, env_slug=env_slug
        ).check_permissions().code_server.restart()

    @sync_to_async
    def workbench_start_local_airflow(self, env_slug):
        WorkbenchBuilder(
            user=self.user, env_slug=env_slug
        ).check_permissions().code_server.enable_local_airflow()

    # Send user notification message
    async def user_notification(self, event):
        message_type = event["message_type"]
        message = event["message"]
        payload = {"message_type": message_type, "message": json.loads(message)}

        # Send message to WebSocket
        await self.send(text_data=json.dumps(payload, default=serialize_datetime))

    # Send environment status message
    async def env_status_change(self, event):
        message_type = event["message_type"]
        message = event["message"]
        payload = {"message_type": message_type, "message": json.loads(message)}

        # Send message to WebSocket
        await self.send(text_data=json.dumps(payload, default=serialize_datetime))
