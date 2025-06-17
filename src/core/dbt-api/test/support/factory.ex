defmodule Support.Factory do
  alias Support.Factories.Airflow
  alias Support.Factories.Datacoves
  alias Support.Factories.Jade

  def insert(type, attrs \\ [], opts \\ []) do
    factory = get_factory(type)
    factory.insert(type, attrs, opts)
  end

  def insert_pair(type, attrs \\ []) do
    factory = get_factory(type)
    factory.insert_pair(type, attrs)
  end

  def insert_list(count, type, attrs \\ []) do
    factory = get_factory(type)
    factory.insert_list(count, type, attrs)
  end

  def params_for(type, attrs \\ []) do
    factory = get_factory(type)
    factory.params_for(type, attrs)
  end

  defp get_factory(type) do
    cond do
      type in [:token, :job_id, :job_run_id, :manifest, :file] ->
        Jade

      type in [
        :account,
        :user,
        :permission,
        :auth_token,
        :project,
        :environment,
        :group,
        :extended_group
      ] ->
        Datacoves

      type in [:dag, :dag_run] ->
        Airflow
    end
  end
end
