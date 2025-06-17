defmodule JadeWeb.API.FallbackController do
  use Phoenix.Controller, formats: [:json]

  import Plug.Conn

  require Logger

  def call(conn, {:error, %Ecto.Changeset{} = changeset}) do
    conn
    |> put_status(:unprocessable_entity)
    |> put_view(json: JadeWeb.ChangesetJSON)
    |> render(:error, changeset: changeset)
  end

  def call(conn, {:error, :unprocessable_entity, message}) do
    conn
    |> put_status(:unprocessable_entity)
    |> put_view(json: JadeWeb.ErrorJSON)
    |> render(:"422", message: message)
  end

  def call(conn, {:error, :not_found}) do
    conn
    |> put_status(:not_found)
    |> put_view(json: JadeWeb.ErrorJSON)
    |> render(:"404")
  end

  def call(conn, {:error, :not_found, message}) do
    conn
    |> put_status(:not_found)
    |> put_view(json: JadeWeb.ErrorJSON)
    |> render(:"404", message: message)
  end

  def call(conn, {:error, :invalid_params}) do
    conn
    |> put_status(:bad_request)
    |> put_view(json: JadeWeb.ErrorJSON)
    |> render(:"400")
  end

  def call(conn, {:error, _error, message}) do
    conn
    |> put_status(:internal_server_error)
    |> JadeWeb.ErrorJSON.send_json(message)
    |> halt()
  end

  def call(conn, {:error, _error}) do
    conn
    |> put_status(:internal_server_error)
    |> put_view(json: JadeWeb.ErrorJSON)
    |> render(:"500")
  end

  def unauthenticated(conn, message) do
    conn
    |> put_status(:unauthorized)
    |> JadeWeb.ErrorJSON.send_json(message)
    |> halt()
  end
end
