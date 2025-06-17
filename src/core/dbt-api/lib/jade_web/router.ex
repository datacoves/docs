defmodule JadeWeb.Router do
  use JadeWeb, :router

  pipeline :browser do
    plug(:accepts, ["html"])
    plug(:fetch_session)
    plug(:fetch_live_flash)
    plug(:put_root_layout, html: {JadeWeb.Layouts, :root})
    plug(:protect_from_forgery)
    plug(:put_secure_browser_headers)
  end

  pipeline :api do
    plug(:accepts, ["json"])
    plug OpenApiSpex.Plug.PutApiSpec, module: JadeWeb.OpenApi.Spec
  end

  scope "/api/v2" do
    pipe_through(:api)

    scope "/accounts/:account_id", JadeWeb.API.V2 do
      pipe_through(JadeWeb.Plugs.AuthenticateApiKey)

      resources("/", AccountController, only: [:show], singleton: true)

      resources("/projects", ProjectController, only: [:index, :show]) do
        resources("/latest-run", Project.LatestJobRunController,
          only: [:show],
          singleton: true
        )
      end

      resources("/environments", EnvironmentController, only: [:index, :show])
      resources("/jobs", JobController, only: [:index, :show])

      resources("/runs", JobRunController, only: [:index, :show]) do
        resources("/artifacts/:artifact", ManifestController, only: [:show], singleton: true)
      end
    end

    scope "/datacoves", JadeWeb.API.Datacoves do
      pipe_through(JadeWeb.Plugs.AuthenticateApiKey)

      resources("/manifests", ManifestController, only: [:create, :show], singleton: true)

      resources "/environments", EnvironmentController, param: :slug, only: [] do
        resources("/files", FileController,
          only: [:create, :show, :update, :delete],
          param: :slug,
          singleton: true
        )
      end

      get("/projects/:project_slug/latest-manifest", ProjectManifestController, :show)
    end

    get("/healthcheck", JadeWeb.API.Datacoves.HealthcheckController, :show, singleton: true)
  end

  # TODO: Remove this scope once we migrated to /api/v2/datacoves
  scope "/api/internal", JadeWeb.API.Datacoves do
    pipe_through([:api])

    get("/healthcheck", HealthcheckController, :show, singleton: true)
  end

  scope "/api/internal", JadeWeb.API.Datacoves do
    pipe_through([:api, JadeWeb.Plugs.AuthenticateApiKey])

    resources("/manifests", ManifestController, only: [:create, :show], singleton: true)

    resources "/environments", EnvironmentController, param: :slug, only: [] do
      resources("/files", FileController,
        only: [:create, :show, :update, :delete],
        param: :slug,
        singleton: true
      )
    end

    get("/projects/:project_slug/latest-manifest", ProjectManifestController, :show)
  end

  scope "/api/v2" do
    pipe_through(:api)
    get("/openapi", OpenApiSpex.Plug.RenderSpec, [])
  end

  scope "/api/v2" do
    pipe_through :browser
    get "/swaggerui", OpenApiSpex.Plug.SwaggerUI, path: "/api/v2/openapi"
  end

  # Enable LiveDashboard in development
  if Application.compile_env(:jade, :dev_routes) do
    # If you want to use the LiveDashboard in production, you should put
    # it behind authentication and allow only admins to access it.
    # If your application does not have an admins-only section yet,
    # you can use Plug.BasicAuth to set up some basic authentication
    # as long as you are also using SSL (which you should anyway).
    import Phoenix.LiveDashboard.Router

    scope "/dev" do
      pipe_through(:browser)

      live_dashboard("/dashboard", metrics: JadeWeb.Telemetry)
    end
  end
end
