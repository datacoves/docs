defmodule Jade.MixProject do
  use Mix.Project

  @version "0.1.0"

  def version, do: @version

  def project do
    [
      app: :jade,
      version: @version,
      elixir: "~> 1.18",
      elixirc_paths: elixirc_paths(Mix.env()),
      start_permanent: Mix.env() == :prod,
      test_paths: ["test", "lib"],
      aliases: aliases(),
      deps: deps()
    ]
  end

  # Configuration for the OTP application.
  #
  # Type `mix help compile.app` for more information.
  def application do
    [
      mod: {Jade.Application, []},
      extra_applications: [:logger, :runtime_tools]
    ]
  end

  # Specifies which paths to compile per environment.
  defp elixirc_paths(:test), do: ["lib", "test/support"]
  defp elixirc_paths(_), do: ["lib"]

  # Specifies your project dependencies.
  #
  # Type `mix help deps` for examples and options.
  defp deps do
    [
      # Phoenix Dependencies
      {:phoenix, "~> 1.7.9"},
      {:phoenix_ecto, "~> 4.4"},
      {:phoenix_html, "~> 4.2"},
      {:phoenix_live_reload, "~> 1.2", only: :dev},
      {:phoenix_live_view, "~> 1.0"},
      {:phoenix_live_dashboard, "~> 0.8.2"},
      {:gettext, "~> 0.20"},
      {:bandit, ">= 0.0.0"},
      {:jason, "~> 1.2"},

      # Heroicons icons
      {:heroicons,
       github: "tailwindlabs/heroicons", tag: "v2.1.1", sparse: "optimized", app: false, compile: false, depth: 1},

      # Build and Styling
      {:esbuild, "~> 0.7", runtime: Mix.env() == :dev},
      {:tailwind, "~> 0.2.0", runtime: Mix.env() == :dev},

      # OpenAPI Documentation
      {:open_api_spex, "~> 3.18"},

      # Database
      {:ecto_sql, "~> 3.10"},
      {:postgrex, ">= 0.0.0"},

      # File Storage
      {:minio, github: "PJUllrich/minio_ex"},

      # AWS S3 Dependencies
      {:ex_aws, "~> 2.5.0"},
      {:ex_aws_s3, "~> 2.5.2"},
      {:poison, "~> 6.0"},
      {:hackney, "~> 1.20.1"},
      {:sweet_xml, "~> 0.7.4"},

      # Azure Blob Dependencies
      {:azurex, "~> 1.1.0"},

      # HTTP Requests
      {:httpoison, "~> 2.2", override: true},

      # Decription of Datacove Configs
      {:fernetex, "~> 0.5.0"},

      # Test Dependencies
      {:floki, ">= 0.30.0", only: :test},
      {:ex_machina, "~> 2.8", only: :test},
      {:assertions, "~> 0.10", only: :test},

      # Telemetry
      {:telemetry_metrics, "~> 1.0"},
      {:telemetry_poller, "~> 1.0"}
    ]
  end

  # Aliases are shortcuts or tasks specific to the current project.
  # For example, to install project dependencies and perform other setup tasks, run:
  #
  #     $ mix setup
  #
  # See the documentation for `Mix` for more info on aliases.
  defp aliases do
    [
      setup: ["deps.get", "ecto.setup", "assets.setup", "assets.build"],
      "ecto.setup": ["ecto.create", "ecto.migrate", "run priv/repo/seeds.exs"],
      "ecto.reset": ["ecto.drop", "ecto.setup"],
      test: ["ecto.create --quiet", "ecto.migrate --quiet", "airflow.migrate --quiet", "test"],
      "test.reset": [
        "ecto.drop",
        "ecto.create --quiet",
        "ecto.migrate --quiet",
        "airflow.migrate --quiet",
        "test"
      ],
      "assets.setup": ["tailwind.install --if-missing", "esbuild.install --if-missing"],
      "assets.build": ["tailwind default", "esbuild default"],
      "assets.deploy": ["tailwind default --minify", "esbuild default --minify", "phx.digest"]
    ]
  end
end
