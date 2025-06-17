defmodule JadeWeb.FileControllerTest do
  use JadeWeb.ConnCase, async: false

  import ExUnit.CaptureLog

  alias Jade.Files.FileRepo

  @fixture_path "test/support/fixtures/manifest.json"
  @fail_fixture_path "test/support/fixtures/fail.txt"

  setup %{conn: conn} do
    attrs = insert_two_accounts_with_repos()
    user = insert(:user, is_service_account: true)

    auth_token =
      insert_auth_token_for_user(user, attrs.account_1, attrs.environment_1, attrs.project_1)

    conn =
      conn |> put_bearer_token(auth_token.key) |> put_req_header("accept", "application/json")

    Map.merge(attrs, %{conn: conn, user: user})
  end

  describe "create file" do
    test "renders file when data is valid", %{conn: conn} = ctx do
      params = %{
        tag: "tag-123",
        file: %Plug.Upload{path: @fixture_path, filename: "filename.json"}
      }

      conn =
        conn
        |> put_req_header("content-type", "multipart/form-data")
        |> post(~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)

      assert %{"slug" => slug} = json_response(conn, 201)["data"]

      file = FileRepo.get_file!(slug)

      assert file.slug == slug
      assert file.filename == "filename.json"
      assert file.tag == "tag-123"
      assert file.path == "/environments/airflow1/files/tag-123/filename.json"
      # The contents are virtual and are stored only in the Jade.Storage bucket
      assert file.contents == nil
    end

    test "upload multiple files at once", %{conn: conn} = ctx do
      params = %{
        files: [
          {"0",
           %{
             tag: "some tag 1",
             file: %Plug.Upload{path: @fixture_path, filename: "filename-1.json"}
           }},
          {"1",
           %{
             tag: "some tag 2",
             file: %Plug.Upload{path: @fixture_path, filename: "filename-2.json"}
           }}
        ]
      }

      conn =
        conn
        |> put_req_header("content-type", "multipart/form-data")
        |> post(~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)

      %{"data" => files} = json_response(conn, 201)

      assert [
               %{
                 "slug" => slug_1,
                 "tag" => "some tag 1",
                 "filename" => "filename-1.json",
                 "contents" => %{"child_map" => %{"seed.balboa.state_codes" => []}},
                 "path" => "/environments/airflow1/files/some-tag-1/filename-1.json",
                 "environment_slug" => "airflow1"
               },
               %{
                 "slug" => slug_2,
                 "tag" => "some tag 2",
                 "filename" => "filename-2.json",
                 "contents" => %{"child_map" => %{"seed.balboa.state_codes" => []}},
                 "path" => "/environments/airflow1/files/some-tag-2/filename-2.json",
                 "environment_slug" => "airflow1"
               }
             ] = files

      file_1 = FileRepo.get_file!(slug_1)

      assert file_1.slug == slug_1
      assert file_1.tag == "some tag 1"
      assert file_1.filename == "filename-1.json"
      assert file_1.path == "/environments/airflow1/files/some-tag-1/filename-1.json"
      assert file_1.contents == nil
      assert file_1.environment_slug == "airflow1"

      file_2 = FileRepo.get_file!(slug_2)

      assert file_2.slug == slug_2
      assert file_2.filename == "filename-2.json"
      assert file_2.tag == "some tag 2"
      assert file_2.path == "/environments/airflow1/files/some-tag-2/filename-2.json"
      assert file_2.contents == nil
      assert file_1.environment_slug == "airflow1"
    end

    test "returns an error and deletes existing files if one file can't be created",
         %{conn: conn} = ctx do
      params = %{
        "files" => [
          {"0",
           %{
             "tag" => "some tag 1",
             "file" => %Plug.Upload{path: @fixture_path, filename: "some filename 1"}
           }},
          {"1",
           %{
             "tag" => "some tag 2",
             "file" => %Plug.Upload{path: @fail_fixture_path, filename: ""}
           }}
        ]
      }

      assert capture_log(fn ->
               assert conn
                      |> post(
                        ~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files",
                        params
                      )
                      |> json_response(422) == %{"errors" => %{"filename" => ["can't be blank"]}}
             end) =~ "Creating multiple files failed:"

      assert {:error, :not_found} = FileRepo.get_file_by(tag: "some tag 1")
      assert {:error, :not_found} = FileRepo.get_file_by(tag: "some tag 2")
    end

    test "allows files with duplicate tags if they are in separate environments",
         %{conn: conn} = ctx do
      insert(:file, tag: "foobar", environment_slug: ctx.environment_1.slug)

      params = %{
        tag: "foobar",
        file: %Plug.Upload{path: @fixture_path, filename: "filename.json"}
      }

      auth_token =
        insert_auth_token_for_user(ctx.user, ctx.account_1, ctx.environment_2, ctx.project_1)

      %{"data" => %{"slug" => slug}} =
        conn
        |> put_bearer_token(auth_token.key)
        |> post(~p"/api/v2/datacoves/environments/#{ctx.environment_2.slug}/files", params)
        |> json_response(201)

      file = FileRepo.get_file!(slug)

      assert file.slug == slug
      assert file.tag == "foobar"
      assert file.filename == "filename.json"
      assert file.path == "/environments/airflow2/files/foobar/filename.json"
      assert file.contents == nil
      assert file.environment_slug == "airflow2"
    end

    test "does not return error if file is repeated and new version is stored",
         %{conn: conn} = ctx do
      insert(:file, tag: "foobar", environment_slug: ctx.environment_1.slug)

      params = %{
        tag: "foobar",
        file: %Plug.Upload{path: @fixture_path, filename: "some filename"}
      }

      assert conn
             |> post(~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)
             |> json_response(201)

      {:ok, files} =
        FileRepo.get_files_by(%{environment_slug: ctx.environment_1.slug, tag: "foobar"})

      assert length(files) == 2
    end

    test "renders errors when data is invalid", %{conn: conn} = ctx do
      params = %{
        tag: "some tag",
        file: %Plug.Upload{path: @fixture_path, filename: ""}
      }

      conn =
        post(conn, ~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)

      assert json_response(conn, 422) == %{"errors" => %{"filename" => ["can't be blank"]}}
    end

    test "returns an error if the file could not be uploaded", %{conn: conn} = ctx do
      params = %{
        tag: "some tag",
        file: %Plug.Upload{path: @fail_fixture_path, filename: "some filename"}
      }

      assert capture_log(fn ->
               assert conn
                      |> post(
                        ~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files",
                        params
                      )
                      |> json_response(422) == %{
                        "errors" => %{
                          "message" => "File upload failed. Please check the error in the logs."
                        }
                      }
             end) =~ "HTTP Request failed - 400 - \"bad request\""
    end
  end

  describe "show/2" do
    setup [:create_file]

    test "returns a file with its contents for a slug", %{conn: conn, jade_file: file} = ctx do
      params = %{slug: file.slug}

      res_file =
        conn
        |> get(~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)
        |> json_response(200)
        |> Map.get("data")

      assert res_file["slug"] == file.slug
      assert res_file["tag"] == file.tag
      assert res_file["filename"] == file.filename
      assert res_file["environment_slug"] == file.environment_slug
      assert res_file["path"] == file.path
      assert %{"child_map" => %{"seed.balboa.state_codes" => []}} = res_file["contents"]
    end

    test "returns a file by its tag", %{conn: conn, jade_file: file} = ctx do
      params = %{tag: file.tag}

      res_file =
        conn
        |> get(~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)
        |> json_response(200)
        |> Map.get("data")

      assert res_file["slug"] == file.slug
      assert %{"child_map" => %{"seed.balboa.state_codes" => []}} = res_file["contents"]
    end

    test "returns latest file based on filename", %{conn: conn, jade_file: file} = ctx do
      file =
        insert(:file,
          tag: file.tag,
          filename: file.filename,
          environment_slug: ctx.environment_1.slug,
          inserted_at: DateTime.utc_now() |> DateTime.add(10, :second)
        )

      params = %{filename: file.filename}

      res_file =
        conn
        |> get(~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)
        |> json_response(200)
        |> Map.get("data")

      assert res_file["slug"] == file.slug
      assert %{"child_map" => %{"seed.balboa.state_codes" => []}} = res_file["contents"]

      assert res_file["filename"] == file.filename
      assert res_file["environment_slug"] == file.environment_slug
      assert res_file["inserted_at"] == file.inserted_at |> DateTime.to_iso8601()
    end

    test "returns an error if the file could not be downloaded", %{conn: conn} = ctx do
      file = insert(:file, path: "/fail-upload", environment_slug: ctx.environment_1.slug)

      params = %{tag: file.tag}

      assert capture_log(fn ->
               assert conn
                      |> get(
                        ~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files",
                        params
                      )
                      |> json_response(422) == %{
                        "errors" => %{
                          "message" => "The request to the storage bucket failed."
                        }
                      }
             end) =~ "HTTP Request failed - 400 - \"bad request\""
    end

    test "returns a 404 if the file does not belong to the requested environment",
         %{conn: conn} = ctx do
      file = insert(:file, environment_slug: "different-env")

      params = %{slug: file.slug}

      assert conn
             |> get(~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)
             |> json_response(404)
    end

    test "returns a 404 if the file wasn't found by its slug", %{conn: conn} = ctx do
      params = %{slug: Ecto.UUID.generate()}

      assert conn
             |> get(~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)
             |> json_response(404)
    end

    test "returns a 404 if the file wasn't found by its tag", %{conn: conn} = ctx do
      params = %{tag: "not-found"}

      assert conn
             |> get(~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)
             |> json_response(404)
    end
  end

  describe "update file" do
    setup [:create_file]

    test "renders file when data is valid", %{conn: conn, jade_file: file} = ctx do
      params = %{
        slug: file.slug,
        tag: "updated tag",
        file: %Plug.Upload{path: @fixture_path, filename: "updated-filename.json"}
      }

      conn = put(conn, ~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)
      assert %{"slug" => slug} = json_response(conn, 200)["data"]

      file = FileRepo.get_file!(slug)

      assert file.slug == slug
      assert file.filename == "updated-filename.json"
      assert file.tag == "updated tag"

      assert file.path ==
               "/environments/#{ctx.environment_1.slug}/files/updated-tag/updated-filename.json"

      # The contents are virtual and are stored only in the Jade.Storage bucket
      assert file.contents == nil
    end

    test "updates a file by its tag", %{conn: conn, jade_file: file} = ctx do
      params = %{
        tag: file.tag,
        file: %Plug.Upload{path: @fixture_path, filename: "updated filename"}
      }

      conn =
        conn
        |> put_req_header("content-type", "multipart/form-data")
        |> put(~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)

      assert %{"slug" => slug} = json_response(conn, 200)["data"]

      file = FileRepo.get_file!(slug)
      assert file.filename == "updated filename"
    end

    test "renders errors when data is invalid", %{conn: conn, jade_file: file} = ctx do
      params = %{
        slug: file.slug,
        tag: "",
        filename: "",
        file: %Plug.Upload{path: @fixture_path}
      }

      conn = put(conn, ~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)

      assert %{
               "errors" => %{
                 "filename" => ["can't be blank"]
               }
             } =
               json_response(conn, 422)
    end

    test "returns an error if the file could not be uploaded",
         %{conn: conn, jade_file: file} = ctx do
      params = %{
        slug: file.slug,
        file: %Plug.Upload{path: @fail_fixture_path, filename: "updated filename"}
      }

      assert capture_log(fn ->
               assert conn
                      |> put(
                        ~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files",
                        params
                      )
                      |> json_response(422) == %{
                        "errors" => %{
                          "message" => "File upload failed. Please check the error in the logs."
                        }
                      }
             end) =~ "HTTP Request failed - 400 - \"bad request\""
    end

    test "returns 404 if the file does not exist", %{conn: conn} = ctx do
      params = %{slug: Ecto.UUID.generate()}

      assert put(conn, ~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)
             |> json_response(404)
    end
  end

  describe "delete file" do
    setup [:create_file]

    test "deletes chosen file by its slug", %{conn: conn, jade_file: file} = ctx do
      params = %{slug: file.slug}

      assert conn
             |> delete(~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)
             |> response(200)

      assert reload(file) == nil
    end

    test "deletes chosen file by its tag", %{conn: conn, jade_file: file} = ctx do
      params = %{tag: file.tag}

      assert conn
             |> delete(~p"/api/v2/datacoves/environments/#{ctx.environment_1.slug}/files", params)
             |> response(200)

      assert reload(file) == nil
    end
  end

  def create_file(%{environment_1: environment_1}) do
    %{jade_file: insert(:file, environment_slug: environment_1.slug)}
  end
end
