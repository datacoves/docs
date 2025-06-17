## Environment variables override
Airflow has a feature that lets you override system's defaults on a per-task basis (see https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/kubernetes.html#pod-override).

__Example "Log level override"__:

```python
"pod_override": k8s.V1Pod(
    spec=k8s.V1PodSpec(
        containers=[
            k8s.V1Container(
                name="base",
                image=f"{IMAGE_REPO}:{IMAGE_TAG}",
                env=[
                    k8s.V1EnvVar(
                        name="AIRFLOW__LOGGING__LOGGING_LEVEL",
                        value="DEBUG"
                    )
                ]
            )
        ]
    )
),
```
