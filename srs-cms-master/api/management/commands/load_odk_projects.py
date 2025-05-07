import os
from django.core.management.base import BaseCommand
from api.models import OdkProject, EtlDocument
from api.common import Utils


class Command(BaseCommand):
    help = "Load ODK Project and Forms."

    def add_arguments(self, parser):
        parser.add_argument(
            "json_files",
            nargs='*',
            type=str,
            help="Paths to the JSON files to load.",
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

        self.stdout.write("Loading ODK Projects and Forms...")

        for json_file in json_files:
            if not os.path.exists(json_file):
                self.stderr.write(self.style.ERROR(f"File not found: {json_file}"))
                return

        total_loaded_odk_projects = 0
        total_loaded_odk_forms = 0
        try:
            for json_file in json_files:
                verbose and self.stdout.write('Loading ODK Project File: {}'.format(json_file))
                json_data = Utils.load_json(json_file)
                for odk_project_json in json_data:
                    project_name = odk_project_json['name']
                    project_id = odk_project_json['project_id']

                    odk_project = OdkProject.objects.filter(name=project_name, project_id=project_id).first()

                    if odk_project:
                        verbose and self.stdout.write(f"OdkProject already exists: {odk_project.name}")
                    else:
                        odk_project = OdkProject.objects.create(
                            name=project_name,
                            project_id=project_id,
                            is_enabled=odk_project_json['is_enabled']
                        )
                        verbose and self.stdout.write(f"Loaded OdkProject: {odk_project.name}")
                        total_loaded_odk_projects += 1

                    # Create ODK Entity Sets
                    for odk_entity_list_json in odk_project_json['odk_entity_lists']:
                        entity_list_name = odk_entity_list_json['name']

                        odk_entity_list = odk_project.odk_entity_lists.filter(name=entity_list_name).first()

                        if odk_entity_list:
                            verbose and self.stdout.write(f"OdkEntityList already exists: {odk_entity_list.name}")
                        else:
                            odk_entity_list = odk_project.odk_entity_lists.create(
                                name=entity_list_name,
                                is_enabled=odk_entity_list_json['is_enabled']
                            )
                            verbose and self.stdout.write(f"Loaded OdkEntityList: {odk_entity_list.name}")

                        # Create Entity List Exporters
                        for odk_entity_list_exporter_json in odk_entity_list_json['odk_entity_list_exporters']:
                            etl_doc_name, etl_doc_version = odk_entity_list_exporter_json['etl_document'].split('|')
                            etl_doc = EtlDocument.objects.filter(name=etl_doc_name, version=etl_doc_version).first()
                            if not etl_doc:
                                raise Exception(
                                    f"EtlDocument does not exist: {odk_entity_list_exporter_json['etl_document']}"
                                )

                            exporter = odk_entity_list_exporter_json['exporter']
                            odk_entity_list_exporter = odk_entity_list.odk_entity_list_exporters.filter(
                                etl_document=etl_doc,
                                exporter=exporter
                            ).first()
                            if odk_entity_list_exporter:
                                verbose and self.stdout.write(
                                    f"OdkEntityListExporter already exists: {odk_entity_list_exporter.exporter}"
                                )
                            else:
                                odk_entity_list_exporter = odk_entity_list.odk_entity_list_exporters.create(
                                    exporter=exporter,
                                    is_enabled=odk_entity_list_exporter_json['is_enabled'],
                                    etl_document=etl_doc
                                )
                                verbose and self.stdout.write(
                                    f"Loaded OdkEntityListExporter: {odk_entity_list_exporter.exporter}"
                                )

                    # Create ODK Forms
                    for odk_form_json in odk_project_json['odk_forms']:
                        odk_form_name = odk_form_json['name']
                        xml_form_id = odk_form_json['xml_form_id']
                        version = odk_form_json['version']

                        odk_form = odk_project.odk_forms.filter(
                            name=odk_form_name,
                            xml_form_id=xml_form_id,
                            version=version
                        ).first()

                        if odk_form:
                            verbose and self.stdout.write(f"OdkForm already exists: {odk_form.name}")
                        else:
                            odk_form = odk_project.odk_forms.create(name=odk_form_name,
                                                                    xml_form_id=xml_form_id,
                                                                    version=version,
                                                                    is_enabled=odk_form_json['is_enabled'])
                            total_loaded_odk_forms += 1
                            verbose and self.stdout.write(f"Loaded OdkForm: {odk_form.name}")

                        # Create ODK Form Importers
                        for odk_form_importer_json in odk_form_json['odk_form_importers']:
                            # Create etl mappings
                            etl_doc_name, etl_doc_version = odk_form_importer_json['etl_document'].split('|')
                            etl_doc = EtlDocument.objects.filter(name=etl_doc_name, version=etl_doc_version).first()

                            if not etl_doc:
                                raise Exception(
                                    f"EtlDocument does not exist: {odk_form_importer_json['etl_document']}"
                                )

                            # Create OdkFormImporter
                            import_order = odk_form_importer_json['import_order']
                            importer = odk_form_importer_json['importer']
                            odk_form_importer = odk_form.odk_form_importers.filter(
                                import_order=import_order,
                                importer=importer,
                                etl_document=etl_doc
                            ).first()

                            if odk_form_importer:
                                verbose and self.stdout.write(
                                    f"ODKFormImporter already exists: {odk_form_importer.importer}"
                                )
                            else:
                                odk_form_importer = odk_form.odk_form_importers.create(
                                    import_order=import_order,
                                    importer=importer,
                                    is_enabled=odk_form_importer_json['is_enabled'],
                                    etl_document=etl_doc,
                                    odk_form=odk_form
                                )
                                verbose and self.stdout.write(
                                    f"Loaded ODKFormImporter: {odk_form_importer.importer}"
                                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Loaded {total_loaded_odk_projects} OdkProjects, {total_loaded_odk_forms} OdkForms."))
        except Exception as ex:
            self.stderr.write(self.style.ERROR(f"An error occurred: {ex}"))
