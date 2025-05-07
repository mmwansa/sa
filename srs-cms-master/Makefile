# Install Python packages.
.PHONY: pip_install
pip_install:
	pipenv install --dev
	pip install --upgrade build


# Install NPM packages.
.PHONY: npm_install
npm_install:
	python manage.py tailwind install


# Generate database migrations
.PHONY: migrations
migrations:
	python manage.py makemigrations
	python manage.py validate_migration


# Run database migrations
.PHONY: migrate
migrate:
	python manage.py migrate


# Creates and seeds the dev database.
.PHONY: init_dev
init_dev:
	python manage.py dev_init_database --migrate --seed


# Creates, seeds, loads test data into the dev database.
.PHONY: init_dev_with_test_data
init_dev_with_test_data:
	python manage.py dev_init_database --migrate --seed --with-test-data


# Creates and seeds the dev database.
.PHONY: dev_generate_test_data
dev_generate_test_data:
	python manage.py dev_generate_test_data


# Seed the dev database.
.PHONY: dev_seed_db
dev_seed_db:
	python manage.py dev_seed_database

dev_seed: dev_seed_db


# Createa a super users in the database.
.PHONY: createsuperuser
createsuperuser:
	python manage.py createsuperuser


# Creates the database, user/pass, and assigns roles.
.PHONY: database
database:
	scripts/mk_database.sh


# Drop the database if it exists and recreate an empty database.
.PHONY: init_database
init_database:
	python manage.py dev_init_database

init_db: init_database


# Drops the database if it exists, recreates an empty database, and runs Django migrations.
.PHONY: init_database_migrate
init_database_migrate:
	python manage.py dev_init_database --migrate

init_db_migrate: init_database_migrate


.PHONY: delete_migrations
delete_migrations:
ifeq ($(OS),Windows_NT)
	del /f /q api\migrations\000*.py
else
	rm -f api/migrations/000*.py
endif


.PHONY: reset_migrations
reset_migrations: delete_migrations
	make init_database
	make migrations
	make migrate


.PHONY: reset_migrations_init_dev
reset_migrations_init_dev: delete_migrations
	make init_database
	make migrations
	python manage.py dev_init_database --migrate --seed


# Kills all connections to the database.
.PHONY: kill_db_connections
kill_db_connections:
	python manage.py dev_init_database --kill-connections


# Run the development server.
.PHONY: runserver
runserver:
	python manage.py runserver


# Build the client.
.PHONY: build_client
build_client:
	python manage.py tailwind build


# Watch the client for changes and automatically rebuild.
.PHONY: watch_client
watch_client:
	python manage.py tailwind start


# Import data from ODK.
.PHONY: test
test:
	pytest


# Import Form Submissions from ODK starting from the last imported date.
.PHONY: odk_import_form_submissions
odk_import_form_submissions:
	python manage.py odk_import_form_submissions


# Import Form Submissions from ODK for ALL dates.
.PHONY: odk_import_form_submissions_all
odk_import_form_submissions_all:
	python manage.py odk_import_form_submissions --start-date 1900-01-01


# Export Entity Lists to ODK.
.PHONY: odk_export_entity_lists
odk_export_entity_lists:
	python manage.py odk_export_entity_lists


###################################################################################################
# Docker Production
###################################################################################################

# Build Production docker image.
.PHONY: docker_compose_build
docker_compose_build:
ifeq ($(OS),Windows_NT)
	PowerShell -ExecutionPolicy Bypass -File scripts\run_with_env.ps1 docker\production\env docker compose -f docker\production\docker-compose.yml build
else
	scripts/run_with_env.sh docker/production/env docker compose -f docker/production/docker-compose.yml build
#	scripts/run_with_env.sh docker/production/env docker compose -f docker/production/docker-compose.yml --progress plain build
endif


# Start Production docker.
.PHONY: docker_compose_up
docker_compose_up:
ifeq ($(OS),Windows_NT)
	PowerShell -ExecutionPolicy Bypass -File scripts\run_with_env.ps1 docker\production\env docker compose -f docker\production\docker-compose.yml up -d
else
	scripts/run_with_env.sh docker/production/env docker compose -f docker/production/docker-compose.yml up -d
#	scripts/run_with_env.sh docker/production/env docker compose -f docker/production/docker-compose.yml --progress plain up
endif


# Stop Production docker.
.PHONY: docker_compose_down
docker_compose_down:
ifeq ($(OS),Windows_NT)
	PowerShell -ExecutionPolicy Bypass -File scripts\run_with_env.ps1 docker\production\env docker compose -f docker\production\docker-compose.yml down
else
	scripts/run_with_env.sh docker/production/env docker compose -f docker/production/docker-compose.yml down
endif


# Run Production docker migrations.
.PHONY: docker_migrate
docker_migrate:
	docker exec -it production-srs-cms-web-1 make migrate


# Create Production super user in docker.
.PHONY: docker_createsuperuser
docker_createsuperuser:
	docker exec -it production-srs-cms-web-1 make createsuperuser


# Connect to Production web container in docker.
.PHONY: docker_bash
docker_bash:
	docker exec -it production-srs-cms-web-1 bash
