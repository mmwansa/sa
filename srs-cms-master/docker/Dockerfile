# Use an official Python runtime as a base image
FROM python:3.12-slim

# Set environment variables to prevent Python from buffering outputs
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_HOME=/app
ENV APP_USER=appuser
ARG DOCKER_ENV_PATH

# Create the app directories
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/static
RUN mkdir $APP_HOME/media

# Create a non-root user for the app to run as
RUN groupadd -r appgroup
RUN useradd -r -g appgroup -m -d $APP_HOME appuser
RUN chown -R appuser:appgroup $APP_HOME

# Set the working directory inside the container
WORKDIR $APP_HOME

# Install system dependencies
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc make curl netcat-traditional nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --root-user-action=ignore --upgrade pip

# Install Pipenv
RUN pip install --root-user-action=ignore --no-cache-dir pipenv gunicorn

# Copy the Pipenv files first for caching
COPY Pipfile Pipfile.lock $APP_HOME/

# Install packages system wide.
RUN pipenv install --deploy --system

# Copy the project into the container
COPY . $APP_HOME/

# Copy entrypoint script
COPY $DOCKER_ENV_PATH/entrypoint.sh $APP_HOME/entrypoint.sh
RUN chmod +x $APP_HOME/entrypoint.sh

# Change ownership of $APP_HOME to non-root user
RUN chown -R appuser:appgroup $APP_HOME

# Switch to non-root user
USER appuser

# Set the default command
ENTRYPOINT ["/bin/sh", "-c", "$APP_HOME/entrypoint.sh"]