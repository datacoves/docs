defmodule JadeWeb.ErrorJSON do
  # If you want to customize a particular status code,
  # you may add your own clauses, such as:
  #
  # def render("500.json", _assigns) do
  #   %{errors: %{message: "Internal Server Error"}}
  # end

  # By default, Phoenix returns the status message from
  # the template name. For example, "404.json" becomes
  # "Not Found".
  def render(template, assigns) do
    message = assigns[:message] || Phoenix.Controller.status_message_from_template(template)
    build_errors(message)
  end

  @doc """
  A small helper function for formatting the json error message.
  This is used in Plugs to put the correct error response body.
  """
  def send_json(conn, message) do
    Phoenix.Controller.json(conn, build_errors(message))
  end

  defp build_errors(message) do
    %{errors: %{message: message}}
  end
end
