defmodule Airflow.ReposTest do
  use Jade.DataCase, async: false

  alias Airflow.Repos
  alias Jade.Environments.EnvironmentRepo

  describe "init/1" do
    test "starts a new repo per airflow-enabled and available environment" do
      _env_airflow_disabled =
        insert(:environment, services: %{"airflow" => %{"enabled" => false}}, slug: "disabled")

      _env_airflow_enabled_wo_pods =
        insert(:environment,
          services: %{"airflow" => %{"enabled" => true}},
          slug: "enabled-wo-pods"
        )

      _env_airflow_enabled_with_pods =
        insert(:environment, services: %{"airflow" => %{"enabled" => true}}, slug: "enabled")

      assert capture_log(fn ->
               pid = start_supervised!({Repos, name: :test1})

               # Starts an Airflow.Repo connection for the "enabled" environment.
               assert [{"enabled", _pid, :worker, [Airflow.Repo]}] =
                        Supervisor.which_children(pid)
             end) =~ "Cannot connect to Airflow repo at:"
    end
  end

  describe "get_repo_for_environment/2" do
    test "returns the repo for an enabled environment" do
      insert(:environment, services: %{"airflow" => %{"enabled" => true}}, slug: "enabled")
      [enabled_env] = EnvironmentRepo.list()

      pid = start_supervised!({Repos, name: :test2})
      assert [{"enabled", repo_pid, :worker, [Airflow.Repo]}] = Supervisor.which_children(pid)

      {:ok, res_pid} = Repos.get_repo_for_environment(enabled_env, pid)
      assert repo_pid == res_pid
    end

    test "returns an error of the env is not enabled" do
      insert(:environment, services: %{"airflow" => %{"enabled" => false}}, slug: "disabled")
      [disabled_env] = EnvironmentRepo.list()

      pid = start_supervised!({Repos, name: :test3})

      {:error, :not_found, "Airflow Repo for Environment disabled not found."} =
        Repos.get_repo_for_environment(disabled_env, pid)
    end

    test "starts a new repo if an environment is enabled but no repo was started during init" do
      pid = start_supervised!({Repos, name: :test4})
      # After init, no child Repos were started
      assert [] = Supervisor.which_children(pid)

      insert(:environment, services: %{"airflow" => %{"enabled" => true}}, slug: "enabled")
      [enabled_env] = EnvironmentRepo.list()

      {:ok, res_pid} = Repos.get_repo_for_environment(enabled_env, pid)

      # After the first call, a child Repos was started
      assert [{"enabled", repo_pid, :worker, [Airflow.Repo]}] = Supervisor.which_children(pid)
      assert repo_pid == res_pid
    end
  end
end
