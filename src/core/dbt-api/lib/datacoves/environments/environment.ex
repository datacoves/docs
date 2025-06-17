defmodule Datacoves.Environments.Environment do
  @moduledoc """
  The Environment Schema as stored in the Datacoves database.
  """
  use Datacoves, :schema

  alias __MODULE__

  schema "projects_environment" do
    field :airbyte_config, :binary
    field :airflow_config, :binary
    field :cluster_id, :integer
    field :dbt_docs_config, :binary
    field :dbt_home_path, :string
    field :dbt_profiles_dir, :string
    field :docker_config_secret_name, :string
    field :docker_config, :binary
    field :docker_registry, :string
    field :internal_services, :map
    field :minio_config, :binary
    field :name, :string
    field :pomerium_config, :binary
    field :profile_id, :integer
    field :quotas, :map
    field :release_id, :integer
    field :release_profile, :string
    field :services, :map
    field :settings, :map
    field :slug, :string
    field :superset_config, :binary
    field :sync, :boolean
    field :type, :string
    field :update_strategy, :string
    field :workspace_generation, :integer

    belongs_to :project, Datacoves.Projects.Project

    field :created_at, :utc_datetime
    field :updated_at, :utc_datetime
  end

  @doc """
  Decrypts a Fernet encrypted field from the Datacoves environment.
  """
  def decrypt_json_field!(%Environment{} = environment, field) do
    Mix.env()
    |> do_decrypt_json_field(environment, field)
  end

  defp do_decrypt_json_field(:test, _environment, _field) do
    %{
      "db" => %{"external" => false}
    }
  end

  defp do_decrypt_json_field(_env, environment, field) do
    ciphertext = Map.get(environment, field)
    plaintext = Fernet.verify!(ciphertext, key: fernet_key(), enforce_ttl: false)
    Jason.decode!(plaintext)
  end

  defp fernet_key(), do: Application.get_env(:jade, :fernet_key)
end
