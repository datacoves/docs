# How to trigger External Kubernetes Jobs from Airflow

This how to will walk you through steps to trigger an external Kubernetes job using Datacoves Managed Airflow. Please be sure to store sensitive variables like API tokens, credentials, or kubeconfig data accordingly instead of hardcoding. 

### Step 1: Request Kubernetes Library Installation  

Let the Datacoves team know you need the `kubernetes` library installed. Please be sure to included the version you would like installed in your request. Sent your request to `support@datacoves.com`.

### Step 2: Add Kubernetes Connection in Airflow

- Someone with Airflow Admin access can add the connection by navigating to the `Admin` Menu and selecting `Connections` in Airflow.
- Provide the following: 
  - `Connection ID` - You will use this in your DAG
  - `Connection Type` - Select  `Kubernetes Cluster Connection` 
  - `Kube config path` 
  - `Namespace` 
  - `Cluster Context`

### Step 3: Create a Python Script for Job Execution  

Create your python script that triggers your Kubernetes job in the `orchestrate/python_scripts/` directory. 
 
**Below is an example script that:**
- Fetches configuration from environment variables and extracts Kubernetes credentials.
- Checks if a previous execution is running and waits for it to complete.
- Deletes old job ifprevious job exists.
- Dynamically creates a new Kubernetes Job based on an existing CronJob.
- Monitors the new job's execution status until completion or failure.

```python
# kubernetes_job_executer.py
'''
This module creates a JOb out of existing Cronjob in Kubernetes and executes and verifies the POD status.
'''

import os
import json
import sys
import time
from urllib.parse import urlparse, unquote_plus
from kubernetes import client, config


kube_conn_url = os.getenv('kube_conn')
namespace = os.getenv('kube_namespace')
cronjob_name = os.getenv('kube_cronjob_name')
context = os.getenv('kube_context')
job_command = os.getenv('job_command')
try:
    job_command = eval(job_command)
except:
    job_command = None
job_name = cronjob_name + "-airflow-run" 

kube_conn_url = unquote_plus(kube_conn_url)
kube_conn_url = kube_conn_url.replace("\\", '')
parsed_url = urlparse(kube_conn_url)
parsed_url = urlparse(parsed_url.query)
data = parsed_url.path
data = data.replace('__extra__=', '').replace("\"{", "{").replace("}\"", "}")
data = json.loads(data)

# Load Kubernetes configuration
config.load_kube_config_from_dict(data['kube_config'],
                                  context=context
                                  )
# Create a Kubernetes API client
v1 = client.CoreV1Api()
batch_v1 = client.BatchV1Api()

def execution_status():
    '''
    Checks if job is already running
    :return:
    '''
    response_dict = list_pods()
    for _, state in response_dict.items():
        if state[1] == job_name:
            return state[0]
    return None

def list_pods():
    '''
    Get a List of Running Pods
    :param cron_name:
    :return:
    '''
    res = v1.list_namespaced_pod(namespace, pretty=True)
    data_dict = {}
    for i in res.items:
        pod_name = i.metadata.name
        pod_status = i.status.phase
        jobname = i.metadata.labels['job-name']
        data_dict[pod_name] = (pod_status, jobname)
    return data_dict


def delete_job():
    '''
    Delete existing job
    :return:
    '''
    data_dict = list_pods()
    for pod_name, state in data_dict.items():
        if state[1] == job_name:
            v1.delete_namespaced_pod(pod_name, namespace, pretty=True)
            batch_v1.delete_namespaced_job(job_name,namespace)

def create_airflow_run(job_command=None):
    '''
    Creates a Job from existing cronjob
    :return:
    '''

    # Get the CronJob object
    cronjob = batch_v1.read_namespaced_cron_job(cronjob_name, namespace)
    if job_command is not None:
        cronjob.spec.job_template.spec.template.spec.containers[0].command = job_command
    # Create a Job from the CronJob
    job = client.V1Job(
        metadata=client.V1ObjectMeta(
            name=cronjob.metadata.name + "-airflow-run",
            owner_references=[
                client.V1OwnerReference(
                    api_version=cronjob.api_version,
                    kind=cronjob.kind,
                    name=cronjob.metadata.name,
                    uid=cronjob.metadata.uid,
                )
            ],
        ),
        spec=cronjob.spec.job_template.spec,
    )

    # Create the Job
    batch_v1.create_namespaced_job(namespace, job)


if __name__ == '__main__':
    JOB_RUNNING = True
    while JOB_RUNNING:
        status = execution_status()
        if status is None:
            JOB_RUNNING = False
            print("No Job is running which is triggered from airflow.")
        else:
            if status.lower() == ('running', 'pending'):
                print(f"******  Already a Job is running for :: {job_name}. waiting for completion......")
                time.sleep(30)
            else:
                JOB_RUNNING = False
                print(f"Last execution status for job {job_name} is :::::: {status}")
                print("Deleting the existing airflow trigger JOB")
                delete_job()
                time.sleep(10)
    print(f"***** Triggering a Kubernetes JOB with job name {job_name}*****")
    create_airflow_run(job_command=job_command)
    time.sleep(10)
    JOB_RUNNING = True
    while JOB_RUNNING:
        status = execution_status()
        if status.lower() in ('running', 'pending'):
            print(f"Already a Job is running for :: {job_name} with status :: {status}."
                  f"\n waiting for completion......")
            time.sleep(30)
        elif status.lower() == 'failed':
            JOB_RUNNING = False
            print(f"for job >> {job_name} final execution status is :::::: {status}")
            sys.exit(1)
        else:
            JOB_RUNNING = False
            print(f"for job >> {job_name} final execution status is :::::: {status}")
```

### Step 4: Call the script in your DAG

```python
""" 
This is a Kubernetes execution test dag
"""

from airflow.decorators import dag
from operators.datacoves.bash import DatacovesBashOperator
from datetime import datetime, timedelta
from airflow.models import Connection
from airflow import settings

def get_connection_string(conn_id):
    session = settings.Session()
    conn = session.query(Connection).filter(Connection.conn_id == conn_id).first()
    if conn:
        return conn.get_uri()
    else:
        return None

kube_connection = get_connection_string("<YOUR_KUBERNETES_CONNECTION_ID>") # Name of your connection ID you set above



default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 3, 6),
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
    'email': [],
    'email_on_failure': True,
    'email_on_retry': False
}
@dag(
    dag_id="Kubernetes_execution_dag",
    schedule_interval=None,  # This DAG runs manually or can be triggered
    default_args=default_args,
    catchup=False,  # Do not backfill this DAG
    tags=["example"]
)
def bash_command_dag():

    bash = DatacovesBashOperator(
        task_id="Execute_Kubernetes_Python_Job",
        bash_command = f"python orchestrate/python_scripts/kubernetes_job_executer.py", # Path to your python file you created above
        retries=0,
        env={
            'kube_conn': kube_connection,
            'kube_namespace': '<YOUR_NAMESPACE>',
            'kube_cronjob_name': '<YOUR_CRONJOB_NAME>',
            'kube_context': '<YOUR_KUBE_CONTEXT>'

            } # These will be used in your script 
    )
    bash
# Instantiate the DAG
bash_command_dag_instance = bash_command_dag()
```
