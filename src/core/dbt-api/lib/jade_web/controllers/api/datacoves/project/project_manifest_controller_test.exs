defmodule JadeWeb.API.Datacoves.ProjectManifestControllerTest do
  use JadeWeb.ConnCase, async: false

  @fixture_path "test/support/fixtures/manifest.json"

  defp path(project_slug) do
    ~p"/api/v2/datacoves/projects/#{project_slug}/latest-manifest"
  end

  setup %{conn: conn} do
    attrs = insert_two_accounts_with_repos()
    insert(:dag_run, repo: attrs.repo_1, run_id: "manual__2023-12-02T09:49:46.105347+00:00")

    user = insert(:user)

    auth_token =
      insert_auth_token_for_user(user, attrs.account_1, attrs.environment_1, attrs.project_1)

    conn = put_bearer_token(conn, auth_token.key)

    Map.merge(attrs, %{conn: conn})
  end

  describe "show/2" do
    test "returns a minimal manifest", ctx do
      content = @fixture_path |> File.read!() |> Jason.decode!()

      # later_manifest =
      insert(:manifest,
        project_id: ctx.environment_1.project_id,
        content: content,
        inserted_at: ~U[2023-01-01 12:00:00Z]
      )

      _earlier_manifest =
        insert(:manifest,
          project_id: ctx.environment_1.project_id,
          content: nil,
          inserted_at: ~U[2023-01-01 01:00:00Z]
        )

      body =
        ctx.conn
        |> get(path(ctx.environment_1.project.slug))
        |> json_response(200)

      # %{
      # id: manifest_id,
      # account_id: manifest_account_id,
      # environment_slug: manifest_environment_slug,
      # dag_id: manifest_dag_id,
      # dag_run_run_id: manifest_dag_run_run_id
      # } = later_manifest

      assert %{
               # "id" => ^manifest_id,
               # "account_id" => ^manifest_account_id,
               # "environment_slug" => ^manifest_environment_slug,
               # "dag_id" => ^manifest_dag_id,
               # "dag_run_id" => ^manifest_dag_run_run_id,
               # "exposures" => %{
               #   "exposure.balboa.customer_loans" => %{
               #     "fqn" => ["balboa", "L4_exposures", "customer_loans"]
               #     # removed other fields for brevity
               #   },
               #   "exposure.balboa.loans_analysis" => %{
               #     "fqn" => ["balboa", "L4_exposures", "loans_analysis"]
               #   }
               # },
               # "group_map" => %{},
               # "groups" => %{},
               "metadata" => %{
                 "generated_at" => "2024-01-18T14:38:12.611300Z",
                 "project_name" => "balboa"
                 # removed other fields for brevity
               },
               "nodes" => %{
                 "model.balboa.base_cases" => %{
                   "database" => "BALBOA_DEV",
                   "fqn" => ["balboa", "L2_bays", "covid_observations", "base_cases"],
                   "schema" => "gomezn"
                 },
                 "model.balboa.country_populations" => %{
                   "database" => "BALBOA_DEV",
                   "fqn" => ["balboa", "L1_inlets", "country_data", "country_populations"],
                   "schema" => "gomezn"
                 }
               }
             } = body
    end

    test "returns an empty map if the manifest has no content", ctx do
      insert(:manifest,
        project_id: ctx.environment_1.project_id,
        content: nil
      )

      body =
        ctx.conn
        |> get(path(ctx.environment_1.project.slug))
        |> json_response(200)

      assert %{
               # "exposures" => nil,
               # "group_map" => nil,
               # "groups" => nil,
               "metadata" => nil,
               "nodes" => nil
             } = body
    end

    test "returns the full manifest if requested", ctx do
      content = @fixture_path |> File.read!() |> Jason.decode!()

      insert(:manifest,
        project_id: ctx.environment_1.project_id,
        content: content
      )

      params = %{
        "trimmed" => false
      }

      body =
        ctx.conn
        |> get(path(ctx.environment_1.project.slug), params)
        |> json_response(200)

      # These fields are excluded from the trimmed version
      assert %{
               "selectors" => _selectors,
               "metrics" => _metrics,
               "sources" => _sources,
               "macros" => _macros,
               "docs" => _docs,
               "disabled" => _disabled
             } = body
    end

    test "returns a 404 if no manifest exists for a given project_slug", ctx do
      %{"errors" => %{"message" => "Not Found"}} =
        ctx.conn
        |> get(path(ctx.environment_1.project.slug))
        |> json_response(404)
    end

    test "returns a 404 if no project exists for a given project_slug", ctx do
      %{
        "errors" => %{"message" => "Invalid Project in Path. You have no accces to this project."}
      } =
        ctx.conn
        |> get(path("fake-project-123"))
        |> json_response(401)
    end
  end
end
