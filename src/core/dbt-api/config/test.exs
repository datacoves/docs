import Config

config :jade,
  ecto_repos: [Jade.Repo, Datacoves.Repo]

# Configure your database
#
# The MIX_TEST_PARTITION environment variable can be used
# to provide built-in test partitioning in CI environment.
# Run `mix help test` for more information.
config :jade, Jade.Repo,
  username: "postgres",
  password: System.get_env("DB_PASS", "password"),
  hostname: "localhost",
  database: "jade_test#{System.get_env("MIX_TEST_PARTITION")}",
  pool: Ecto.Adapters.SQL.Sandbox,
  pool_size: 2

config :jade, Datacoves.Repo,
  priv: "test/datacoves_repo",
  username: "postgres",
  password: System.get_env("DB_PASS", "password"),
  hostname: "localhost",
  database: "datacoves_test#{System.get_env("MIX_TEST_PARTITION")}",
  pool: Ecto.Adapters.SQL.Sandbox,
  pool_size: 2

config :jade, Airflow.Repo,
  priv: "test/airflow_repo",
  username: "postgres",
  password: System.get_env("DB_PASS", "password"),
  hostname: "localhost",
  database: "airflow_test#{System.get_env("MIX_TEST_PARTITION")}",
  pool: Ecto.Adapters.SQL.Sandbox,
  pool_size: 2

config :jade,
  http_adapter: Support.Mocks.HTTPoisonMock,
  datacoves_verify_url: "https://api.datacoveslocal.com/api/datacoves/verify"

# We don't run a server during test. If one is required,
# you can enable the server option below.
config :jade, JadeWeb.Endpoint,
  http: [ip: {127, 0, 0, 1}, port: 4002],
  secret_key_base: "iwIf4aWKSisvWt92wor1xaAKry7fiPHRhWZQQkoA0dTFm1sN2o8Xwt4/i2Enxu22",
  server: false

config :jade, internal_bearer_token: "internal_bearer_token"

# Print only warnings and errors during test
config :logger, level: :warning

# Initialize plugs at runtime for faster test compilation
config :phoenix, :plug_init_mode, :runtime
