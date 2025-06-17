#!/bin/bash
# Exit the script immediately if any command returns a non-zero exit status.
set -e

if [ "$1" = "dev" ]; then

  echo "Starting in Dev Mode"

  export MIX_ENV="dev"
  export PHX_SERVER="false"
  export PHX_ENDPOINT="false"

  mix deps.get
  iex -S mix phx.server

elif [ "$1" = "shell" ]; then

  echo "Creating a Shell in the Production Server"

  iex --name "shell@127.0.0.1" --cookie $IEX_COOKIE --remsh "server@127.0.0.1"

else

  echo "Starting in Prod Web Server Mode"

  echo "Connecting to the database with the following environment variables"
  echo "Jade database:"
  echo "DB_USER: ${DB_USER}"
  echo "DB_PASS: hidden"
  echo "DB_HOST: ${DB_HOST}"
  echo "DB_NAME: ${DB_NAME}"

  echo "Datacoves database:"
  echo "DATACOVES_DB_USER: ${DATACOVES_DB_USER}"
  echo "DATACOVES_DB_PASS: hidden"
  echo "DATACOVES_DB_HOST: ${DATACOVES_DB_HOST}"
  echo "DATACOVES_DB_NAME: ${DATACOVES_DB_NAME}"

  export MIX_ENV="prod"
  export PHX_SERVER="true"
  export PHX_ENDPOINT="true"

  mix do ecto.create, ecto.migrate
  elixir --name "server@127.0.0.1" --cookie $IEX_COOKIE -S mix phx.server

fi
