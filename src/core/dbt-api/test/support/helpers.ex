defmodule Support.Helpers do
  import Support.Factory

  def insert_two_accounts_with_repos() do
    account_1 = insert(:account)

    # Create an Environment/Database for the main account
    project_1 = insert(:project, account: account_1)

    environment_1 =
      insert(:environment,
        project: project_1,
        services: %{"airflow" => %{"enabled" => true}},
        slug: "airflow1"
      )

    # Create an Environment/Database for the another account
    account_2 = insert(:account)
    project_2 = insert(:project, account: account_2)

    environment_2 =
      insert(:environment,
        project: project_2,
        services: %{"airflow" => %{"enabled" => true}},
        slug: "airflow2"
      )

    pid = ExUnit.Callbacks.start_supervised!(Airflow.Repos)
    children = Supervisor.which_children(pid)

    repo_1 =
      Enum.find_value(children, fn {id, pid, :worker, _repo} -> id == "airflow1" && pid end)

    repo_2 =
      Enum.find_value(children, fn {id, pid, :worker, _repo} -> id == "airflow2" && pid end)

    %{
      account_1: account_1,
      account_2: account_2,
      project_1: project_1,
      project_2: project_2,
      environment_1: environment_1,
      environment_2: environment_2,
      repo_1: repo_1,
      repo_2: repo_2
    }
  end

  def insert_auth_token_for_user(user, account, environment, project) do
    extended_group =
      insert(:extended_group, account: account, environment: environment, project: project)

    insert(:group, users: [user], extended_group: extended_group)
    insert(:auth_token, user: user)
  end
end
