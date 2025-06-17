defmodule JadeWeb.Plugs.Utils do
  @moduledoc """
  Holds utility functions for custom Plugs.
  """

  import Plug.Conn

  def get_bearer_token(conn) do
    authorization_header =
      conn
      |> get_req_header("authorization")
      |> List.first()

    case authorization_header do
      "Bearer " <> token -> {:ok, String.trim(token)}
      "Token " <> token -> {:ok, String.trim(token)}
      _ -> {:error, :missing_api_key}
    end
  end
end
