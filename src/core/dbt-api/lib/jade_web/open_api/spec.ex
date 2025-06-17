defmodule JadeWeb.OpenApi.Spec do
  alias OpenApiSpex.{Components, Info, SecurityScheme, OpenApi, Paths, Server}
  alias JadeWeb.{Endpoint, Router}
  @behaviour OpenApi

  @impl OpenApi
  def spec do
    server_url = build_server_url()

    %OpenApi{
      servers: [
        # Populate the Server info from a phoenix endpoint
        %Server{url: server_url}
      ],
      info: %Info{
        title: "Jade",
        version: Jade.MixProject.version()
      },
      components: %Components{
        securitySchemes: %{"authorization" => %SecurityScheme{type: "http", scheme: "bearer"}}
      },
      security: [%{"authorization" => []}],
      # Populate the paths from a phoenix router
      paths: Paths.from_router(Router)
    }
    # Discover request/response schemas from path specs
    |> OpenApiSpex.resolve_schema_modules()
  end

  defp build_server_url() do
    uri = Endpoint.struct_url()
    path = Endpoint.path("") || "/"
    host = "dbt." <> uri.host
    uri = %{uri | path: path, host: host}
    URI.to_string(uri)
  end
end
