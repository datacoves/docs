## DAG logs were serialized with a newer version of pickle than the installed on Airflow webserver

### Logs

```
Traceback (most recent call last):
  File "/home/airflow/.local/bin/airflow", line 8, in <module>
    sys.exit(main())
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/__main__.py", line 38, in main
    args.func(args)
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/cli/cli_parser.py", line 51, in command
    return func(*args, **kwargs)
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/utils/cli.py", line 99, in wrapper
    return f(*args, **kwargs)
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/cli/commands/scheduler_command.py", line 75, in scheduler
    _run_scheduler_job(args=args)
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/cli/commands/scheduler_command.py", line 46, in _run_scheduler_job
    job.run()
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/jobs/base_job.py", line 244, in run
    self._execute()
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/jobs/scheduler_job.py", line 739, in _execute
    self._run_scheduler_loop()
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/jobs/scheduler_job.py", line 827, in _run_scheduler_loop
    num_queued_tis = self._do_scheduling(session)
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/jobs/scheduler_job.py", line 909, in _do_scheduling
    callback_to_run = self._schedule_dag_run(dag_run, session)
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/jobs/scheduler_job.py", line 1151, in _schedule_dag_run
    schedulable_tis, callback_to_run = dag_run.update_state(session=session, execute_callbacks=False)
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/utils/session.py", line 68, in wrapper
    return func(*args, **kwargs)
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/models/dagrun.py", line 522, in update_state
    info = self.task_instance_scheduling_decisions(session)
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/utils/session.py", line 68, in wrapper
    return func(*args, **kwargs)
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/models/dagrun.py", line 640, in task_instance_scheduling_decisions
    tis = list(self.get_task_instances(session=session, state=State.task_states))
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/utils/session.py", line 68, in wrapper
    return func(*args, **kwargs)
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/models/dagrun.py", line 441, in get_task_instances
    return tis.all()
  File "/home/airflow/.local/lib/python3.7/site-packages/sqlalchemy/orm/query.py", line 2683, in all
    return self._iter().all()
  File "/home/airflow/.local/lib/python3.7/site-packages/sqlalchemy/engine/result.py", line 1335, in all
    return self._allrows()
  File "/home/airflow/.local/lib/python3.7/site-packages/sqlalchemy/engine/result.py", line 408, in _allrows
    rows = self._fetchall_impl()
  File "/home/airflow/.local/lib/python3.7/site-packages/sqlalchemy/engine/result.py", line 1243, in _fetchall_impl
    return self._real_result._fetchall_impl()
  File "/home/airflow/.local/lib/python3.7/site-packages/sqlalchemy/engine/result.py", line 1636, in _fetchall_impl
    return list(self.iterator)
  File "/home/airflow/.local/lib/python3.7/site-packages/sqlalchemy/orm/loading.py", line 120, in chunks
    fetch = cursor._raw_all_rows()
  File "/home/airflow/.local/lib/python3.7/site-packages/sqlalchemy/engine/result.py", line 400, in _raw_all_rows
    return [make_row(row) for row in rows]
  File "/home/airflow/.local/lib/python3.7/site-packages/sqlalchemy/engine/result.py", line 400, in <listcomp>
    return [make_row(row) for row in rows]
  File "/home/airflow/.local/lib/python3.7/site-packages/sqlalchemy/sql/sqltypes.py", line 1816, in process
    return loads(value)
  File "/home/airflow/.local/lib/python3.7/site-packages/dill/_dill.py", line 275, in loads
    return load(file, ignore, **kwds)
  File "/home/airflow/.local/lib/python3.7/site-packages/dill/_dill.py", line 270, in load
    return Unpickler(file, ignore=ignore, **kwds).load()
  File "/home/airflow/.local/lib/python3.7/site-packages/dill/_dill.py", line 472, in load
    obj = StockUnpickler.load(self)
ValueError: unsupported pickle protocol: 5
```

### Solution

Connect to scheduler or triggerer pod and then remove DAG by running:

```sh
airflow dags delete <dag id>
```
