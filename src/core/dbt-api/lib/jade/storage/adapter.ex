defmodule Jade.Storage.Adapter do
  @moduledoc """
  The Behaviour for Storage Adapters.
  """

  @type filename :: binary()
  @type bucket :: binary()
  @type contents :: binary()
  @type response :: map()

  @callback upload(bucket, filename, contents) :: {:ok, response} | {:error, any()}
  @callback download(bucket, filename) :: {:ok, contents} | {:error, any()}
  @callback delete(bucket, filename) :: {:ok, response} | {:error, any()}
end
