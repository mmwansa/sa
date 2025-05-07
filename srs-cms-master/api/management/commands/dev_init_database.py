import psycopg2
from django.core.management.base import BaseCommand
from django.core.management import call_command
from config.env import Env


class Command(BaseCommand):
    help = 'Initialize the Development Database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--migrate',
            action='store_true',
            help='Run migrations'
        )

        parser.add_argument(
            '--kill-connections',
            action='store_true',
            help='Kill database connections.'
        )

        parser.add_argument(
            '--seed',
            action='store_true',
            help='Seed the database.'
        )

        parser.add_argument('--with-test-data',
                            default=False,
                            action='store_true',
                            help='Load test data.')

    def handle(self, *args, **kwargs):
        migrate = kwargs['migrate']
        kill_connections = kwargs['kill_connections']
        seed = kwargs['seed']
        with_test_data = kwargs['with_test_data']

        if kill_connections:
            self.db_kill_connections()
        else:
            self.db_kill_connections()

            if self.db_exists():
                self.stdout.write(self.style.SUCCESS("Database {} exists. Dropping...".format(self.db_name)))
                self.drop_database()

            if not self.db_exists():
                self.stdout.write(
                    self.style.SUCCESS("Database {} does not exist. Creating...").format(self.db_name))
                self.create_database()
            else:
                self.stdout.write(self.style.ERROR("Database {} still exists..".format(self.db_name)))

            if self.db_exists():
                if migrate:
                    self.stdout.write(self.style.SUCCESS("Running migrations..."))
                    call_command("migrate")
                    self.stdout.write(self.style.SUCCESS("Database initialization completed with migrations."))
                else:
                    self.stdout.write(self.style.WARNING("Database initialization completed without migrations."))

                if seed:
                    self.stdout.write(self.style.SUCCESS("Seeding Database..."))
                    if with_test_data:
                        call_command("dev_seed_database", "--with-test-data")
                    else:
                        call_command("dev_seed_database")
                    self.stdout.write(self.style.SUCCESS("Database initialization completed with seeding."))
                else:
                    self.stdout.write(self.style.WARNING("Database initialization completed without seeding."))

    @property
    def db_host(self):
        return Env.db_host()

    @property
    def db_port(self):
        return Env.db_port()

    @property
    def db_name(self):
        return Env.db_name()

    @property
    def db_user(self):
        return Env.db_user()

    @property
    def db_pass(self):
        return Env.db_pass()

    def db_conn(self, dbname='postgres'):
        """Gets a database connection."""
        try:
            connection = psycopg2.connect(
                dbname=dbname,
                user=self.db_user,
                password=self.db_pass,
                host=self.db_host,
                port=self.db_port
            )
            return connection
        except psycopg2.Error as e:
            return None

    def db_exists(self):
        """Check if the srs_cms database exists."""
        try:
            connection = self.db_conn(dbname=self.db_name)
            if connection:
                connection.close()
            return connection is not None
        except psycopg2.OperationalError:
            return False

    def db_kill_connections(self):
        """Kill all database connections."""
        try:
            connection = self.db_conn()
            connection.autocommit = True
            cursor = connection.cursor()
            cursor.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid()')
            cursor.close()
            connection.close()
            self.stdout.write(self.style.SUCCESS('Killed Database Connections.'))
        except psycopg2.Error as e:
            self.stderr.write(self.style.ERROR('Failed to Kill Database Connections'))

    def create_database(self):
        """Create the srs_cms database."""
        try:
            connection = self.db_conn()
            connection.autocommit = True
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE {self.db_name};")
            cursor.close()
            connection.close()

            connection = self.db_conn(dbname=self.db_name)
            connection.autocommit = True
            cursor = connection.cursor()
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            cursor.close()
            connection.close()

            self.stdout.write(self.style.SUCCESS(f"Database {self.db_name} created successfully."))
        except psycopg2.Error as e:
            self.stderr.write(self.style.ERROR(f"Failed to create database: {e}"))

    def drop_database(self):
        """Drop the srs_cms database."""
        try:
            connection = self.db_conn()
            connection.autocommit = True
            cursor = connection.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS {self.db_name}")
            cursor.close()
            connection.close()
            self.stdout.write(self.style.SUCCESS(f"Database {self.db_name} dropped successfully."))
        except psycopg2.Error as e:
            self.stderr.write(self.style.ERROR(f"Failed to drop database: {e}"))
