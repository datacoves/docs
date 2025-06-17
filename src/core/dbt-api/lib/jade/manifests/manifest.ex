defmodule Jade.Manifests.Manifest do
  use Jade, :schema

  schema "manifests" do
    field :slug, :binary_id
    field :tag, :string
    field :account_id, :integer
    field :project_id, :integer
    field :environment_slug, :string
    # This is the DAG ID we get from Airflow (e.g. "yaml_sample_dag")
    field :dag_id, :string
    # This is the internal, integer ID for the DAGRun (e.g. 1)
    field :dag_run_id, :integer
    # This is the DAGRun ID we get from Airflow (e.g. "manual__2023-12-02T09:49:46.105347+00:00")
    field :dag_run_run_id, :string
    field :content, :map, load_in_query: false

    belongs_to :job_run, Jade.JobRunIds.JobRunId, foreign_key: :job_run_id

    timestamps(type: :utc_datetime)
  end

  def filepath(%__MODULE__{id: id, job_run_id: nil} = m) when not is_nil(id) do
    "accounts/#{m.account_id}/environments/#{m.environment_slug}/manifests/#{m.id}/manifest.json"
  end

  def filepath(%__MODULE__{dag_run_run_id: dag_run_run_id} = m) when is_binary(dag_run_run_id) do
    safe_dag_run_run_id = String.replace(m.dag_run_run_id, ~r/[_:.+]/, "-")

    "accounts/#{m.account_id}/environments/#{m.environment_slug}/dags/#{m.dag_id}/dag_runs/#{safe_dag_run_run_id}/manifest.json"
  end

  @doc false
  def changeset(manifest, attrs) do
    manifest
    |> cast(attrs, [
      :tag,
      :account_id,
      :project_id,
      :environment_slug,
      :dag_id,
      :dag_run_id,
      :dag_run_run_id,
      :job_run_id,
      :content
    ])
    |> validate_required([
      :account_id,
      :project_id,
      :environment_slug
    ])
    |> unique_constraint([:environment_slug, :tag], error_key: :tag)
  end
end
