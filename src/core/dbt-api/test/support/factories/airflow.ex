defmodule Support.Factories.Airflow do
  alias Airflow.Dags.Dag
  alias Airflow.DagRuns.DagRun

  def insert(record, attrs \\ [], opts \\ [])

  def insert(:dag, attrs, _opts) do
    %Dag{
      dag_id: "python_sample_dag_#{Enum.random(1..1000)}",
      default_view: "graph",
      description: "Sample python dag dbt run",
      fileloc: "/opt/airflow/dags/repo/orchestrate/dags/python_sample_dag.py",
      has_import_errors: false,
      has_task_concurrency_limits: false,
      is_active: true,
      is_paused: false,
      is_subdag: false,
      last_expired: nil,
      last_parsed_time: ~U[2023-10-26 14:14:57Z],
      last_pickled: nil,
      max_active_runs: 16,
      max_active_tasks: 16,
      next_dagrun_create_after: ~U[2024-01-01 00:00:00Z],
      next_dagrun_data_interval_end: ~U[2024-01-01 00:00:00Z],
      next_dagrun_data_interval_start: ~U[2023-01-01 00:00:00Z],
      next_dagrun: ~U[2023-01-01 00:00:00Z],
      owners: "airflow",
      pickle_id: nil,
      root_dag_id: nil,
      schedule_interval: "0 0 1 */12 *",
      scheduler_lock: nil,
      timetable_description: "At 00:00 on day 1 of the month every 12 months"
    }
    |> merge_and_insert(attrs)
  end

  def insert(:dag_run, attrs, _opts) do
    %DagRun{
      dag_id: "sample_project_#{Enum.random(1..100)}",
      execution_date: utc_datetime_now(),
      state: :queued,
      run_id: "manual__#{DateTime.utc_now()}",
      external_trigger: true,
      conf: <<128, 5, 125, 148, 46>>,
      end_date: nil,
      start_date: nil,
      run_type: "manual",
      last_scheduling_decision: nil,
      dag_hash: "random-dag-hash",
      creating_job_id: nil,
      queued_at: utc_datetime_now(),
      data_interval_start: gen_datetime(-2),
      data_interval_end: gen_datetime(-1),
      log_template_id: 1
    }
    |> merge_and_insert(attrs)
  end

  def insert_pair(record, attrs, opts \\ []), do: insert_list(2, record, attrs, opts)

  def insert_list(count, record, attrs, opts \\ []) do
    Enum.map(1..count//1, fn _idx -> insert(record, attrs, opts) end)
  end

  def params_for(_record, _attrs), do: raise("Not implemented")

  defp gen_datetime(shift, date \\ Date.utc_today()) do
    date |> Date.add(shift) |> DateTime.new!(~T[12:00:00]) |> DateTime.truncate(:second)
  end

  defp utc_datetime_now() do
    DateTime.utc_now() |> DateTime.truncate(:second)
  end

  defp merge_and_insert(struct, attrs) when is_list(attrs) do
    merge_and_insert(struct, Map.new(attrs))
  end

  defp merge_and_insert(struct, attrs) do
    {repo, attrs} = Map.pop(attrs, :repo)
    struct = Map.merge(struct, attrs)

    Airflow.Repo.put_dynamic_repo(repo)
    Ecto.Adapters.SQL.Sandbox.mode(Airflow.Repo, :manual)
    Ecto.Adapters.SQL.Sandbox.checkout(Airflow.Repo)
    Airflow.Repo.insert!(struct)
  end
end
