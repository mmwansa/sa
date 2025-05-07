# Project Structure

```
srs-cms
  - api         # Django App - Database Schema/Models, REST API, Workers.
  - client      # Django App - Client code
  - config      # Django App Configuration
  - docker      # Docker files
  - theme       # Django App - TailwindCSS
  - scripts     # Helper scripts
  - tests       # Django App Tests
```

# Docker

Deploy with docker: [docker/ReadMe.md](docker/ReadMe.md)

# Development

## Prerequisites

- PostgreSQL
- Node
- NPM
- Python 3.12
- pipenv

## Initial Setup

1. Run `make pip_install`
2. Run `make npm_install`
3. Copy `.env.template` to `.env`.
4. Edit `.env` and set the variables for your environment.
5. Run `make database` (for linux, or see below for Windows)
6. Run `make migrate`
7. Run `make createsuperuser`

### Make Database - Windows

1. Open a `cmd` window with administrative privileges.
2. Run: `psql -U postgres -h localhost -p 5432`
3. Run: `CREATE USER <db_user> WITH PASSWORD '<db_pass>';` (Change `<db_user>` and `<db_pass>` to your credentials)
4. Run: `GRANT ALL PRIVILEGES ON DATABASE dev_srs_cms TO <db_user>;` (Change `<db_user>` to your database username)
5. Exit psql and run: `make init_dev`

## Migrations

1. Create the Models in `api/models/`
2. Run `make migrations`
3. Run `make migrate`

## Start the Development Server

1. Run `make runserver` and `make watch_client` in separate terminals.
2. Goto `http://127.0.0.1:8000` and login with the user/pass created in 'make createsuperuser'.

## Common Commands

- Create and seed the dev database: `make init_dev` or `make init_dev_with_test_data`
- Reset Database to Empty: `make init_database`
- Reset Database to Empty and Run Migrations: `make init_database_migrate`
- Reset the Database and rebuild Migrations: `make reset_migrations`
- Reset the Database, rebuild Migrations, and seed database: `make reset_migrations_init_dev`
- Kill all Database Connections: `make kill_db_connections`
- Make Migrations: `make migrations`
- Apply Migrations: `make migrate`
- Import Form Submissions from ODK: `make odk_import_form_submissions`
    - > Development: Set `DEV_ODK_IMPORT_USE_EXISTING_IF_MISSING=True` in `.env` to use existing
      Provinces/Clusters/Areas if not found during import.
- Export Entity Lists to ODK: `make odk_export_entity_lists`
- Run Tests: `make test`

## Data Loading Commands

Load Permissions and Groups: `./manage.py load_permissions`

Load Provinces: `./manage.py load_provinces path/to/provinces.csv --verbose`
> Development: Set `DEV_LOAD_PROVINCES_CSV` in `.env` and it will be loaded during `make init_dev`.

Load Clusters: `./manage.py load_clusters path/to/clusters.csv --verbose`
> Development: Set `DEV_LOAD_CLUSTERS_CSV` in `.env` and it will be loaded during `make init_dev`.

Load Areas: `./manage.py load_areas path/to/areas.csv --verbose`
> Development: Set `DEV_LOAD_AREAS_CSV` in `.env` and it will be loaded during `make init_dev`.

Load Staff: `./manage.py load_staff path/to/staff.csv --verbose`
> Development: Set `DEV_LOAD_STAFF_CSV` in `.env` and it will be loaded during `make init_dev`.

## Reference make app (for windows)

- `https://gnuwin32.sourceforge.net/packages/make.htm`
- Add file location for make.exe to "Path" environment variable.

## Resources

- Tailwind CSS: https://tailwindcss.com/docs/styling-with-utility-classes
- DaisyUI: https://daisyui.com/components/
- Icons: https://heroicons.com
