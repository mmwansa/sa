import os
from django.core.management.base import BaseCommand
from api.models import EtlDocument
from api.common import Utils


class Command(BaseCommand):
    help = "Load ETL Documents and Mappings."

    def add_arguments(self, parser):
        parser.add_argument(
            "json_files",
            nargs='*',
            type=str,
            help="Paths to the JSON files to load.",
        )
        parser.add_argument(
            "--etl-document",
            type=str,
            help="For single file loading only. The ETL Document ID to load the mappings into.",
        )
        parser.add_argument(
            '--verbose',
            default=False,
            action='store_true',
            help='Print extra details.'
        )

    def handle(self, *args, **kwargs):
        json_files = list(map(lambda path: Utils.expand_path(path), Utils.to_list(kwargs["json_files"])))
        verbose = kwargs['verbose']
        etl_document_id = kwargs['etl_document']

        self.stdout.write("Loading ETL Documents and Mappings...")

        for json_file in json_files:
            if not os.path.exists(json_file):
                self.stderr.write(self.style.ERROR(f"File not found: {json_file}"))
                return

        if etl_document_id and len(json_files) > 1:
            self.stderr.write(self.style.ERROR("ETL Document only allowed when loading a single file"))
            return

        total_loaded = 0
        try:
            for json_file in json_files:
                verbose and self.stdout.write('Loading ETL File: {}'.format(json_file))
                json_data = Utils.load_json(json_file)
                for etl_doc_json in json_data:
                    name = etl_doc_json['name']
                    version = etl_doc_json['version']
                    source_root = etl_doc_json['source_root']

                    if etl_document_id:
                        etl_document = EtlDocument.find_by(id=etl_document_id)
                        if not etl_document:
                            self.stderr.write(self.style.ERROR(f"ETL Document ID not found: {etl_document_id}"))
                            return
                    else:
                        etl_document = EtlDocument.objects.filter(name=name, version=version).first()

                    if etl_document and not etl_document_id:
                        verbose and self.stdout.write(
                            f"EtlDocument already exists: {etl_document.name}, Version: {etl_document.version}"
                        )
                    else:
                        if not etl_document:
                            etl_document = EtlDocument.objects.create(
                                name=name,
                                version=version,
                                source_root=source_root)
                            verbose and self.stdout.write(
                                f"Loaded EtlDocument: {etl_document.name}, Version: {etl_document.version}"
                            )
                            total_loaded += 1
                        else:
                            etl_document.source_root = source_root
                            etl_document.save()

                    for mapping_json in etl_doc_json['mappings']:
                        source_name = mapping_json['source_name']
                        target_name = mapping_json['target_name']

                        if source_name and target_name and source_name != 'TODO':
                            etl_mapping = etl_document.etl_mappings.filter(
                                source_name=source_name,
                                target_name=target_name
                            ).first()

                            if etl_mapping:
                                verbose and self.stdout.write(
                                    f"EtlMapping already exists: {etl_mapping.source_name} -> {etl_mapping.target_name}"
                                )
                            else:
                                etl_mapping = etl_document.etl_mappings.create(
                                    source_name=source_name,
                                    target_name=target_name,
                                    target_type=mapping_json['target_type'],
                                    default=mapping_json['default'],
                                    transform=mapping_json['transform'],
                                    is_primary_key=mapping_json['is_primary_key'],
                                    is_enabled=mapping_json['is_enabled'],
                                    is_required=mapping_json['is_required']
                                )
                                verbose and self.stdout.write(
                                    f"Loaded EtlMapping: {etl_mapping.source_name} -> {etl_mapping.target_name}"
                                )

            self.stdout.write(self.style.SUCCESS(f"Loaded {total_loaded} ETL Documents."))
        except Exception as ex:
            self.stderr.write(self.style.ERROR(f"An error occurred: {ex}"))
