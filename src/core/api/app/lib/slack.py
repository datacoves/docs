from django.conf import settings
from slack_sdk import WebClient

client = None
if settings.SLACK_BOT_TOKEN:
    client = WebClient(token=settings.SLACK_BOT_TOKEN)


def post_slack_message(channel, text, blocks, thread_ts=None):
    response = None
    if client:
        response = client.chat_postMessage(
            channel=channel, text=text, blocks=blocks, thread_ts=thread_ts
        )
    return response
