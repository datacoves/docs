import json
import logging
import threading

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from lib.utils import serialize_datetime

logger = logging.getLogger(__name__)


def run_in_thread(consumer: str, group_name: str, message_type: str, payload: dict):
    """Function to send messages to a Channels group in a separate thread."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": consumer,
            "message_type": message_type,
            "message": json.dumps(payload, default=serialize_datetime),
        },
    )


class DjangoChannelNotify:
    def __init__(
        self, consumer: str, group_name: str, message_type: str, payload: dict
    ):
        self.consumer = consumer
        self.group_name = group_name
        self.message_type = message_type
        self.payload = payload
        self.thread = None  # To reference the thread

    def __enter__(self):
        self.thread = threading.Thread(
            target=run_in_thread,
            args=(self.consumer, self.group_name, self.message_type, self.payload),
            daemon=True,  # Allows the thread to close with the application
        )
        self.thread.start()
        return self  # Can be used `as context` if necessary

    def __exit__(self, exc_type, exc_value, traceback):
        if self.thread:
            self.thread.join(timeout=2)  # Waits a bit and does not block indefinitely
