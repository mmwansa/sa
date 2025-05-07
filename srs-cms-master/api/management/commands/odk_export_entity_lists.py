import sys
from django.core.management.base import BaseCommand
from api.odk.exporters.entity_lists.entity_list_exporter import EntityListExporter


class Command(BaseCommand):
    help = 'Export Entity Lists to ODK.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--projects',
            nargs='*',
            type=int,
            help='OdkProject IDs to export.'
        )

        parser.add_argument(
            '--entity-lists',
            nargs='*',
            type=str,
            help='OdkEntityList IDs to export.'
        )

        parser.add_argument(
            '--exporters',
            nargs='*',
            type=str,
            help='Only execute these exporters.'
        )

        parser.add_argument(
            '--out-dir',
            type=str,
            help='Path to save each exported file.'
        )

        parser.add_argument(
            '--verbose',
            default=False,
            action='store_true',
            help='Print extra details.'
        )

    def handle(self, *args, **kwargs):
        project_ids = kwargs['projects']
        odk_entity_lists_ids = kwargs['entity_lists']
        exporters = kwargs['exporters']
        out_dir = kwargs['out_dir']
        verbose = kwargs['verbose']

        odk_export_result = EntityListExporter(
            odk_projects=project_ids,
            odk_entity_lists=odk_entity_lists_ids,
            exporters=exporters,
            out_dir=out_dir,
            verbose=verbose
        ).execute()

        if odk_export_result.errors:
            sys.exit(1)
        else:
            sys.exit(0)
