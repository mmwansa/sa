#!/bin/bash

# Load utils.
source "$(cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)"/utils.sh

echo "Configuring Database"

# Create the database if it doesn't exist
if db_exists; then
    echo "Database '$DB_NAME' already exists."
else
    echo "Creating database '$DB_NAME'..."
    sudo -u postgres createdb "$DB_NAME"
    echo "Database '$DB_NAME' created."
fi

# Create the user if it doesn't exist
if user_exists; then
    echo "User '$DB_USER' already exists."
else
    if [[ -z "$DB_PASS" ]]; then
        echo "Creating user '$DB_USER' without password..."
        sudo -u postgres psql -c "CREATE USER \"$DB_USER\";"
    else
        echo "Creating user '$DB_USER' with password..."
        sudo -u postgres psql -c "CREATE USER \"$DB_USER\" WITH PASSWORD '$DB_PASS';"
    fi
    echo "User '$DB_USER' created."
fi

# Grant privileges
echo "Granting all privileges on database '$DB_NAME' to user '$DB_USER'..."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE \"$DB_NAME\" TO \"$DB_USER\";"
sudo -u postgres psql -h "$DB_HOST" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
echo "Privileges granted."

echo "PostgreSQL database and user setup completed successfully."
