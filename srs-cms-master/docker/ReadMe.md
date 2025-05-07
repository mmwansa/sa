# Initial Setup

- Git pull the `srs-cms` repository or download the code.
- Change to the project directory `cd srs-cms`
- Copy `docker/production/env.template` to `docker/production/env` and set the variables.
- Edit `docker/production/nginx.config` for your environment.
- Build the docker image: `make docker_compose_build`
- Start the app: `make docker_compose_up`
- Create a superuser: `make docker_createsuperuser`

# Start/Stop the App

- Start: `make docker_compose_up`
    - App URL: [http://localhost](http://localhost)
- Stop: `make docker_compose_down`

# Misc. Commands

- Get a shell in the `web` container:  `make docker_bash`