import sys
import argparse
from datetime import datetime
from django.core.management.base import BaseCommand
from api.odk.importers.form_submissions.form_submission_importer import FromSubmissionImporter


class Command(BaseCommand):
    help = 'Imports Form Submissions from ODK.'

    def add_arguments(self, parser):
        def valid_date(date_string):
            """Validate and parse a date string into a datetime object."""
            try:
                return datetime.strptime(date_string, '%Y-%m-%d')
            except ValueError:
                raise argparse.ArgumentTypeError(f"Invalid date format: '{date_string}'. Use YYYY-MM-DD.")

        parser.add_argument(
            "--start-date",
            type=valid_date,
            help="Import form submissions starting from this date. Format: YYYY-MM-DD."
        )

        parser.add_argument(
            "--end-date",
            type=valid_date,
            help="Import form submissions before this date. Format: YYYY-MM-DD."
        )

        parser.add_argument(
            '--projects',
            nargs='*',
            type=int,
            help='OdkProject IDs'
        )

        parser.add_argument(
            '--forms',
            nargs='*',
            type=str,
            help='OdkForm IDs'
        )

        parser.add_argument(
            '--form-versions',
            nargs='*',
            type=str,
            help='Only import these form versions.'
        )

        parser.add_argument(
            '--importers',
            nargs='*',
            type=str,
            help='Only execute these importers.'
        )

        parser.add_argument(
            '--out-dir',
            type=str,
            help='Path to save each imported file from ODK.'
        )

        parser.add_argument(
            '--verbose',
            default=False,
            action='store_true',
            help='Print extra details.'
        )

    def handle(self, *args, **kwargs):
        project_ids = kwargs['projects']
        form_ids = kwargs['forms']
        form_versions = kwargs['form_versions']
        importers = kwargs['importers']
        out_dir = kwargs['out_dir']
        start_date = kwargs['start_date']
        end_date = kwargs['end_date']
        verbose = kwargs['verbose']

        odk_import_result = FromSubmissionImporter(
            odk_projects=project_ids,
            odk_forms=form_ids,
            form_versions=form_versions,
            importers=importers,
            import_start_date=start_date,
            import_end_date=end_date,
            out_dir=out_dir,
            verbose=verbose
        ).execute()

        if odk_import_result.errors:
            sys.exit(1)
        else:
            sys.exit(0)
