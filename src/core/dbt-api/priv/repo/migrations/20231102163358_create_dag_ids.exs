defmodule Jade.Repo.Migrations.CreateJobIds do
  use Ecto.Migration

  def change do
    create table(:job_ids) do
      add(:environment_id, :integer)
      add(:dag_id, :string)
    end

    create(unique_index(:job_ids, [:environment_id, :dag_id]))
  end
end
