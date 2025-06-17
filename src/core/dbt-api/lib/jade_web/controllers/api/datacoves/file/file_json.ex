defmodule JadeWeb.API.Datacoves.FileJSON do
  alias Jade.Files.File

  def index(%{files: files}) do
    %{data: for(file <- files, do: data(file))}
  end

  def show(%{file: file}) do
    %{data: data(file)}
  end

  defp data(%File{} = file) do
    %{
      slug: file.slug,
      filename: file.filename,
      tag: file.tag,
      contents: encode_contents(file.contents),
      environment_slug: file.environment_slug,
      path: file.path,
      inserted_at: file.inserted_at
    }
  end

  defp encode_contents(contents) when is_binary(contents) do
    Jason.Fragment.new(contents)
  end

  defp encode_contents(contents), do: contents
end
