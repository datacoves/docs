defmodule JadeWeb.API.V2.ManifestJSON do
  @doc """
  Renders a single manifest.
  """
  def show(%{file: file}) do
    %{data: file}
  end
end
