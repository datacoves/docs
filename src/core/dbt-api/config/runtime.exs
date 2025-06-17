import Config

# config/runtime.exs is executed for all environments, including
# during releases. It is executed after compilation and before the
# system starts, so it is typically used to load production configuration
# and secrets from environment variables or elsewhere. Do not define
# any compile-time configuration in here, as it won't be applied.
# The block below contains prod specific runtime configuration.

# ## Using releases
#
# If you use `mix release`, you need to explicitly enable the server
# by passing the PHX_SERVER=true when you start it:
#
#     PHX_SERVER=true bin/jade start
#
# Alternatively, you can use `mix phx.gen.release` to generate a `bin/server`
# script that automatically sets the env var above.
if System.get_env("PHX_SERVER") in ~w(true 1) do
  config :jade, JadeWeb.Endpoint, server: true
end

config :jade,
  connect_to_airflow: System.get_env("CONNECT_TO_AIRFLOW", "false") in ~w(true 1),
  start_endpoint: System.get_env("PHX_ENDPOINT", "true") in ~w(true 1)

if config_env() == :test do
  config :jade, :storage,
    bucket: "jade-dev",
    adapter: Jade.Storage.Minio,
    minio_url: "http://localhost:9000",
    minio_access_key: "minioadmin",
    minio_secret_key: "minioadmin"
end

if config_env() != :test do
  config :jade,
    fernet_key: System.fetch_env!("FERNET_KEY"),
    datacoves_verify_url: System.get_env("DATACOVES_VERIFY_URL")

  storage_adapter =
    case System.get_env("STORAGE_ADAPTER", "minio") do
      "minio" -> :minio
      "s3" -> :s3
      "blob" -> :blob
    end

  if storage_adapter == :minio do
    config :jade, :storage,
      adapter: Jade.Storage.Minio,
      minio_url: System.get_env("MINIO_URL", "http://localhost:9000"),
      minio_access_key: System.get_env("MINIO_ACCESS_KEY", "minioadmin"),
      minio_secret_key: System.get_env("MINIO_SECRET_KEY", "minioadmin"),
      bucket: System.get_env("MINIO_BUCKET_NAME", "jade-dev")
  end

  if storage_adapter == :s3 do
    config :ex_aws,
      access_key_id: [System.fetch_env!("S3_ACCESS_KEY"), :instance_role],
      secret_access_key: [System.fetch_env!("S3_SECRET_ACCESS_KEY"), :instance_role],
      region: System.fetch_env!("S3_REGION")

    config :jade, :storage,
      adapter: Jade.Storage.S3,
      bucket: System.get_env("S3_BUCKET_NAME", "jade-dev")
  end

  if storage_adapter == :blob do
    if connection_string = System.get_env("BLOB_STORAGE_ACCOUNT_CONNECTION_STRING") do
      config :azurex, Azurex.Blob.Config,
        default_container: System.fetch_env!("BLOB_CONTAINER"),
        storage_account_connection_string: connection_string
    else
      config :azurex, Azurex.Blob.Config,
        default_container: System.fetch_env!("BLOB_CONTAINER"),
        storage_account_name: System.fetch_env!("BLOB_STORAGE_ACCOUNT_NAME"),
        storage_account_key: System.fetch_env!("BLOB_STORAGE_ACCOUNT_KEY")
    end

    config :jade, :storage,
      adapter: Jade.Storage.Blob,
      bucket: System.fetch_env!("BLOB_CONTAINER")
  end
end

if config_env() == :prod do
  internal_bearer_token = System.fetch_env!("INTERNAL_BEARER_TOKEN")
  config :jade, internal_bearer_token: internal_bearer_token

  maybe_ipv6 = if System.get_env("ECTO_IPV6") in ~w(true 1), do: [:inet6], else: []

  maybe_jade_url = System.get_env("DB_URL")
  maybe_datacoves_url = System.get_env("DATACOVES_DB_URL")

  if maybe_jade_url do
    config :jade, Jade.Repo, url: maybe_jade_url
  else
    config :jade, Jade.Repo,
      username: System.get_env("DB_USER", "postgres"),
      password: System.get_env("DB_PASS", "password"),
      hostname: System.get_env("DB_HOST", "localhost"),
      database: System.get_env("DB_NAME", "jade_dev"),
      port: String.to_integer(System.get_env("DB_PORT", "5432")),
      pool_size: String.to_integer(System.get_env("POOL_SIZE") || "10"),
      socket_options: maybe_ipv6
  end

  if maybe_datacoves_url do
    config :jade, Datacoves.Repo, url: maybe_datacoves_url
  else
    config :jade, Datacoves.Repo,
      username: System.get_env("DATACOVES_DB_USER", "postgres"),
      password: System.get_env("DATACOVES_DB_PASS", "password"),
      hostname: System.get_env("DATACOVES_DB_HOST", "localhost"),
      database: System.get_env("DATACOVES_DB_NAME", "datacoves"),
      port: String.to_integer(System.get_env("DATACOVES_DB_PORT", "5432")),
      pool_size: String.to_integer(System.get_env("DATACOVES_POOL_SIZE") || "10"),
      socket_options: maybe_ipv6
  end

  # Configure optional SSL for all Repos
  config :jade, Jade.Repo,
    ssl: String.to_existing_atom(System.get_env("DB_SSL_ENABLED", "false")),
    ssl_opts: [
      verify: :verify_none
    ]

  config :jade, Datacoves.Repo,
    ssl: String.to_existing_atom(System.get_env("DB_SSL_ENABLED", "false")),
    ssl_opts: [
      verify: :verify_none
    ]

  config :jade, Airflow.Repo,
    ssl: String.to_existing_atom(System.get_env("DB_SSL_ENABLED", "false")),
    ssl_opts: [
      verify: :verify_none
    ]

  # The secret key base is used to sign/encrypt cookies and other secrets.
  # A default value is used in config/dev.exs and config/test.exs but you
  # want to use a different value for prod and you most likely don't want
  # to check this value into version control, so we use an environment
  # variable instead.
  secret_key_base =
    System.get_env("SECRET_KEY_BASE") ||
      raise """
      environment variable SECRET_KEY_BASE is missing.
      You can generate one by calling: mix phx.gen.secret
      """

  host = System.get_env("PHX_HOST") || "example.com"
  port = String.to_integer(System.get_env("PORT") || "4000")

  config :jade, JadeWeb.Endpoint,
    url: [host: host, port: 443, scheme: "https"],
    check_origin: [
      host,
      "*.core.svc.cluster.local"
    ],
    http: [
      # Enable IPv6 and bind on all interfaces.
      # Set it to  {0, 0, 0, 0, 0, 0, 0, 1} for local network only access.
      # See the documentation on https://hexdocs.pm/plug_cowboy/Plug.Cowboy.html
      # for details about using IPv6 vs IPv4 and loopback vs public addresses.
      ip: {0, 0, 0, 0, 0, 0, 0, 0},
      port: port
    ],
    secret_key_base: secret_key_base

  # ## SSL Support
  #
  # To get SSL working, you will need to add the `https` key
  # to your endpoint configuration:
  #
  #     config :jade, JadeWeb.Endpoint,
  #       https: [
  #         ...,
  #         port: 443,
  #         cipher_suite: :strong,
  #         keyfile: System.get_env("SOME_APP_SSL_KEY_PATH"),
  #         certfile: System.get_env("SOME_APP_SSL_CERT_PATH")
  #       ]
  #
  # The `cipher_suite` is set to `:strong` to support only the
  # latest and more secure SSL ciphers. This means old browsers
  # and clients may not be supported. You can set it to
  # `:compatible` for wider support.
  #
  # `:keyfile` and `:certfile` expect an absolute path to the key
  # and cert in disk or a relative path inside priv, for example
  # "priv/ssl/server.key". For all supported SSL configuration
  # options, see https://hexdocs.pm/plug/Plug.SSL.html#configure/1
  #
  # We also recommend setting `force_ssl` in your endpoint, ensuring
  # no data is ever sent via http, always redirecting to https:
  #
  #     config :jade, JadeWeb.Endpoint,
  #       force_ssl: [hsts: true]
  #
  # Check `Plug.SSL` for all available options in `force_ssl`.

  # ## Configuring the mailer
  #
  # In production you need to configure the mailer to use a different adapter.
  # Also, you may need to configure the Swoosh API client of your choice if you
  # are not using SMTP. Here is an example of the configuration:
  #
  #     config :jade, Jade.Mailer,
  #       adapter: Swoosh.Adapters.Mailgun,
  #       api_key: System.get_env("MAILGUN_API_KEY"),
  #       domain: System.get_env("MAILGUN_DOMAIN")
  #
  # For this example you need include a HTTP client required by Swoosh API client.
  # Swoosh supports Hackney and Finch out of the box:
  #
  #     config :swoosh, :api_client, Swoosh.ApiClient.Hackney
  #
  # See https://hexdocs.pm/swoosh/Swoosh.html#module-installation for details.
end
