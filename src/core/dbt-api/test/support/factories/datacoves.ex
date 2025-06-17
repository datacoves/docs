defmodule Support.Factories.Datacoves do
  use ExMachina.Ecto, repo: Datacoves.Repo

  def account_factory do
    %Datacoves.Accounts.Account{
      created_at: ~U[2023-10-25 08:12:01Z],
      updated_at: ~U[2023-10-25 08:12:01Z],
      name: "Local",
      settings: %{},
      deactivated_at: nil,
      subscription: %{},
      subscription_updated_at: nil,
      slug: "local",
      created_by_id: 1,
      plan_id: nil,
      trial_ends_at: nil,
      trial_started_at: nil,
      customer_id: nil,
      workers_execution_limit: %{"airbyte" => 36000, "airflow" => 36000},
      approve_billing_events: true,
      notifications_enabled: %{"billing" => false, "cluster" => false},
      cancelled_subscription: %{},
      developer_licenses: 0
    }
  end

  def user_factory do
    %Datacoves.Users.User{
      eid: "b4046cab-d625-4294-9ba8-a109e4ad0c7f",
      created_at: DateTime.utc_now(),
      updated_at: DateTime.utc_now(),
      password: "",
      last_login: DateTime.utc_now(),
      email: "test@test.com",
      name: "Test McTester",
      avatar: nil,
      deactivated_at: nil,
      is_superuser: true,
      settings: %{},
      is_service_account: false,
      slug: "test"
    }
  end

  def group_factory do
    %Datacoves.Groups.Group{
      name: "some group"
    }
  end

  def extended_group_factory do
    %Datacoves.Groups.ExtendedGroup{
      account: build(:account),
      group: build(:group),
      environment: build(:environment),
      project: build(:project),
      name: "Local Account Admin",
      identity_groups: ["ADMIN-TEST"],
      role: "account_admin"
    }
  end

  def permission_factory do
    %Datacoves.Permissions.Permission{
      name: "test.com:env123|service:resource|write",
      content_type_id: 1,
      codename: "write_resource"
    }
  end

  def auth_token_factory do
    key = for _ <- 0..39, into: "", do: <<Enum.random(~c"0123456789abcdef")>>

    %Datacoves.AuthTokens.AuthToken{
      key: key,
      created: DateTime.utc_now()
    }
  end

  def project_factory do
    %Datacoves.Projects.Project{
      account: build(:account),
      repository_id: Enum.random(1..1000),
      name: "Fake Project #{Enum.random(1..1000)}",
      slug: "fake-project-#{Enum.random(1..1000)}",
      release_branch: "main",
      clone_strategy: "http_clone",
      deploy_credentials: "gAAAAABl-very-long-string",
      settings: %{},
      deploy_key_id: nil,
      ci_home_url: nil,
      ci_provider: nil,
      validated_at: nil,
      created_at: DateTime.utc_now(),
      updated_at: DateTime.utc_now()
    }
  end

  def environment_factory do
    %Datacoves.Environments.Environment{
      airbyte_config: "long-base64-string",
      airflow_config: "long-base64-string",
      cluster_id: 1,
      dbt_docs_config: "long-base64-string",
      dbt_home_path: "transform",
      dbt_profiles_dir: "automate",
      docker_config_secret_name: "docker-config-datacovesprivate",
      docker_config: "long-base64-string",
      docker_registry: "",
      internal_services: %{"minio" => %{"enabled" => false}},
      minio_config: "long-base64-string",
      name: "Development",
      pomerium_config: "long-base64-string",
      profile_id: 1,
      quotas: %{},
      release_id: 55,
      release_profile: "dbt-snowflake",
      services: %{
        "airbyte" => %{"enabled" => false},
        "airflow" => %{"enabled" => false},
        "code-server" => %{
          "enabled" => true,
          "unmet_preconditions" => [],
          "valid" => true
        },
        "dbt-docs" => %{
          "enabled" => true,
          "unmet_preconditions" => [],
          "valid" => true
        },
        "superset" => %{"enabled" => false}
      },
      settings: %{},
      slug: "dev123",
      superset_config: "long-base64-string",
      sync: true,
      type: "dev",
      update_strategy: "freezed",
      workspace_generation: 1,
      project: build(:project),
      created_at: ~U[2023-11-07 13:47:14Z],
      updated_at: ~U[2023-11-07 13:47:26Z]
    }
  end
end
