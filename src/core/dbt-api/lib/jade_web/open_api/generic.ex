defmodule JadeWeb.OpenApi.Generic do
  alias OpenApiSpex.Schema

  alias JadeWeb.OpenApi.Schemas

  # Schema types

  def integer(opts \\ []), do: to_schema([type: :integer] ++ opts)
  def string(opts \\ []), do: to_schema([type: :string] ++ opts)
  def boolean(opts \\ []), do: to_schema([type: :boolean] ++ opts)

  def datetime(opts \\ []), do: to_schema([type: :string, format: :"date-time"] ++ opts)

  def datetime_unix(opts \\ []) do
    to_schema([type: :integer, description: "Unix Timestamp in Seconds"] ++ opts)
  end

  def map(opts \\ []) do
    to_schema([type: :object] ++ opts)
  end

  def array_of(schema, opts \\ []) do
    opts = [type: :array, items: schema] ++ opts
    to_schema(opts)
  end

  def one_of(schemas, _opts \\ []) do
    %OpenApiSpex.Schema{
      oneOf: schemas
    }
  end

  def enum(values, opts \\ []) do
    opts = [type: :string, enum: values] ++ opts
    to_schema(opts)
  end

  def nullable(module) do
    %OpenApiSpex.Schema{
      nullable: true,
      allOf: [module]
    }
  end

  defp to_schema(opts) do
    # Make all fields nullable by default.
    opts = Keyword.put_new(opts, :nullable, true)
    struct(Schema, opts)
  end

  # Responses

  def response(schema, name \\ nil)

  def response(schema, nil) do
    name = schema |> to_string() |> String.split(".") |> List.last()
    {name, "application/json", schema}
  end

  def response(schema, name) do
    {name, "applicatin/json", schema}
  end

  def ok(), do: response(Schemas.SuccessResponse, "SuccessResponse")
  def not_found(), do: response(Schemas.ErrorResponse, "NotFoundError")
  def unauthorized(), do: response(Schemas.ErrorResponse, "UnauthorizedError")
end
