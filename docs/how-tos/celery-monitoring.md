# Celery monitoring

For authoritative, more detailed information, see [celery's monitoring guide](https://docs.celeryq.dev/en/stable/userguide/monitoring.html).


## UI

We run the flower UI at `https://flower.{cluster_domain}`. You can see executed
tasks by clicking on tasks, or navigating to `https://flower.{cluster_domain}/tasks`.
You'll want to sort tasks to see the latest Started or Received at the top.
You can filter by task using the Search input. The UI doesn't refresh live.
Increasing the number of shown entries can be helpful.


## CLI

From a core-api pod (`kcc exec -it $api_pod_name -- bash`) you can invoke
celery inspect. One useful thing to do is check the stats.

```
celery -A datacoves inspect stats
```

Here's an excerpt from the output.

```
...
        "total": {
            "billing.tasks.inform_billing_events": 113,
            "billing.tasks.tally_account_resource_usage": 1,
            "billing.tasks.tally_resource_usage": 1,
            "celery.backend_cleanup": 1,
            "clusters.workspace.sync_task": 1211,
            "iam.tasks.clear_tokens": 1,
            "iam.tasks.remove_missing_user_groups": 1,
            "notifications.tasks.send_slack_notification": 7,
            "projects.tasks.delete_unused_project_keys": 1,
            "projects.tasks.remove_unused_environments": 1,
            "projects.tasks.remove_unused_user_volumes": 1,
            "projects.tasks.stop_sharing_codeservers": 38,
            "projects.tasks.turn_off_unused_workspaces": 1134
        },
        "uptime": 68132
...
```

The uptime is 68132 seconds, and the sync_task has run 1211 times, so there's
been one run every 56 seconds in average.
