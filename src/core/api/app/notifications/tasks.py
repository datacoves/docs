from celery.utils.log import get_task_logger
from notifications.models import AccountNotification, Notification

from datacoves.celery import app

logger = get_task_logger(__name__)


@app.task
def send_email_notifications(account_notification_id):
    logger.info(
        f"Sending email notification for account notification id: {account_notification_id}"
    )
    account_notification: AccountNotification = AccountNotification.objects.get(
        id=account_notification_id
    )
    account_notification.send_email()


@app.task
def send_slack_notification(notification_id):
    logger.info(f"Sending slack notification for notification id: {notification_id}")
    notification: Notification = Notification.objects.get(id=notification_id)
    notification.send_slack()


@app.task
def send_slack_account_notification(account_notification_id):
    logger.info(
        f"Sending slack account notification for account notification id: {account_notification_id}"
    )
    account_notification: AccountNotification = AccountNotification.objects.get(
        id=account_notification_id
    )
    account_notification.send_slack()
