defmodule Jade.Files.File do
  use Jade, :schema

  @primary_key {:slug, :binary_id, autogenerate: true}
  @derive {Phoenix.Param, key: :slug}
  schema "files" do
    field(:tag, :string)
    field(:filename, :string)
    field(:environment_slug, :string)
    field(:contents, :string, virtual: true)
    field(:path, :string)

    timestamps(type: :utc_datetime)
  end

  @doc false
  def changeset(file, attrs) do
    file
    |> cast(attrs, [:tag, :filename, :environment_slug, :contents])
    |> validate_required([:tag, :filename, :environment_slug, :contents])
    |> unique_constraint([:environment_slug, :tag], error_key: :tag)
    |> put_path()
  end

  defp put_path(%Ecto.Changeset{valid?: true} = changeset) do
    environment_slug = get_field(changeset, :environment_slug)
    tag = changeset |> get_field(:tag) |> String.replace(~r/[\s_:.+]/, "-")
    filename = changeset |> get_field(:filename) |> String.replace(~r/[\s_:+]/, "-")

    path = "/environments/#{environment_slug}/files/#{tag}/#{filename}"
    put_change(changeset, :path, path)
  end

  defp put_path(changeset), do: changeset
end
