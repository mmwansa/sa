#!/bin/bash

# Directory of this script.
THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Directory of the calling script.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[1]}" )" &> /dev/null && pwd )"

# Root project path.
PROJECT_ROOT=$(realpath "$THIS_SCRIPT_DIR/..")

# Root scripts path.
SCRIPTS_ROOT=$PROJECT_ROOT/scripts

# Root api path.
API_ROOT=$PROJECT_ROOT/api

# Path to the .env file
DOT_ENV_PATH="$PROJECT_ROOT/.env"
# Source the .env file to load environment variables.
source "$DOT_ENV_PATH"

# Check if required environment variable are set.
function db_env_set() {
  if [[ -z "$DB_NAME" || -z "$DB_USER" ]]; then
      echo "Error: Missing required parameters in: $DOT_ENV_PATH"
      exit 1
  fi
}

# Check if the database exists.
function db_exists() {
    db_env_set
    psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1
}

# Check if the user exists in database.
function user_exists() {
    db_env_set
    psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1
}