defmodule :"Elixir.Jade.Repo.Migrations.Allow-multifile-upload" do
  use Ecto.Migration
  @disable_ddl_transaction true
  @disable_migration_lock true

  def change do
    drop_if_exists unique_index(:files, [:environment_slug, :tag])

    create_if_not_exists index(:files, [:environment_slug, :filename, :tag])
    create_if_not_exists index(:files, [:environment_slug, :filename])
    create_if_not_exists index(:files, [:environment_slug, :tag])
  end
end
