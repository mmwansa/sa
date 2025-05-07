import os
import importlib.util
from django.core.management.base import BaseCommand
from django.db.migrations.operations.special import RunSQL
from pathlib import Path


class Command(BaseCommand):
    help = "Ensure the first operation in the migration creates pg_trgm."

    def handle(self, *args, **options):
        try:
            migration_path = 'api/migrations/0001_initial.py'
            sql = 'CREATE EXTENSION IF NOT EXISTS pg_trgm;'

            migration_name = os.path.splitext(os.path.basename(migration_path))[0]
            spec = importlib.util.spec_from_file_location(migration_name, migration_path)
            migration = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration)

            operations = migration.Migration.operations
            if operations and isinstance(operations[0], RunSQL) and operations[0].sql.strip() == sql.strip():
                self.stdout.write(self.style.SUCCESS("pg_trgm exists."))
                return

            pg_trgm_operation = """        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS pg_trgm;",
            reverse_sql="DROP EXTENSION IF EXISTS pg_trgm;",
        ),"""
            migration_file = Path(migration_path)
            content = migration_file.read_text()

            updated_content = content.replace(
                "operations = [",
                f"operations = [\n{pg_trgm_operation}",
            )

            # Write the updated content back to the file
            migration_file.write_text(updated_content)
            self.stdout.write(self.style.SUCCESS(f"Added the pg_trgm {migration_path}."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to update the migration file: {e}"))
