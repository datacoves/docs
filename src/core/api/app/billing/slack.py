from django.conf import settings

from lib.slack import post_slack_message


def report_event_to_slack(event, cluster):
    label = "[TEST] " if cluster.is_local else ""
    text = f"{label}A new billing event requiring approval was just created."
    blocks = [
        {
            "type": "section",
            "text": {"text": text, "type": "mrkdwn"},
            "fields": [
                {"type": "mrkdwn", "text": "*Account*"},
                {"type": "mrkdwn", "text": "*Event Type*"},
                {"type": "plain_text", "text": event.account.name},
                {"type": "plain_text", "text": event.get_event_type_display()},
            ],
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "Review events"},
                "url": f"https://api.{cluster.domain}/panel/billing"
                "/event/?approval_status__exact=P",
            },
        }
    ]
    post_slack_message(settings.SLACK_BILLING_CHANNEL, text, blocks)
