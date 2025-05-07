import os
from api.common import Utils
from api.odk import OdkConfig
from api.odk.exporters.entity_lists.entity_list_export_result import EntityListExportResult
from api.models import Death, OdkEntityListExporter


class VaPreloadExporter:
    def __init__(self, odk_entity_list_exporter, out_dir=None, verbose=False):
        self.odk_config = OdkConfig.from_env()
        # The project ID has to be set here otherwise odk_client.entities.merge will fail even if given a project_id.
        # This is a bug in pyodk.
        self.odk_client = self.odk_config.client(
            project_id=odk_entity_list_exporter.odk_entity_list.odk_project.project_id)
        self.odk_entity_list_exporter = odk_entity_list_exporter
        self.out_dir = Utils.expand_path(out_dir) if out_dir else None
        self.verbose = verbose is True
        self.result = EntityListExportResult()

    def validate_before_execute(self):
        """
        Validate before executing the export.

        Returns:
            True if valid, otherwise False.
        """
        if not isinstance(self.odk_entity_list_exporter, OdkEntityListExporter):
            self.result.error('ODK Entity List Exporter not set.', console=True)
            return False

        if not self.odk_entity_list_exporter.etl_document:
            self.result.error('ETL Document not set. {} {}'.format(
                self.odk_entity_list_exporter.__class__.__name__,
                self.odk_entity_list_exporter.id
            ), console=True)
            return False
        else:
            etl_mappings = self.get_etl_mappings()
            if not etl_mappings:
                self.result.error('ETL Document Mappings not set or enabled. {}: {} ({})'.format(
                    self.odk_entity_list_exporter.etl_document.__class__.__name__,
                    self.odk_entity_list_exporter.etl_document.name,
                    self.odk_entity_list_exporter.etl_document.id
                ), console=True)
                return False
            else:
                primary_key_mappings = [m for m in etl_mappings if m.is_primary_key]
                if not primary_key_mappings:
                    self.result.error('ETL Document Mappings does not have primary key(s) set.. {}: {} ({})'.format(
                        self.odk_entity_list_exporter.etl_document.__class__.__name__,
                        self.odk_entity_list_exporter.etl_document.name,
                        self.odk_entity_list_exporter.etl_document.id
                    ), console=True)
                    return False
        return True

    def get_etl_mappings(self):
        elt_document = self.odk_entity_list_exporter.etl_document
        etl_mappings = elt_document.etl_mappings.filter(is_enabled=True).order_by('-is_primary_key')
        return etl_mappings

    def execute(self):
        try:
            self.result.info('Exporting VA Scheduled Deaths...')
            if not self.validate_before_execute():
                return self.result

            scheduled_deaths = Death.objects.filter(death_status=Death.DeathStatus.VA_SCHEDULED)
            va_preload_data = []
            for scheduled_death in scheduled_deaths:
                record = {}
                label_fields = []
                for etl_mapping in self.get_etl_mappings():
                    has_source_field = etl_mapping.has_source_name(scheduled_death)
                    if etl_mapping.is_required and not has_source_field:
                        self.result.error(
                            'ETL Record does not have a field named {}. ETL Record: {}'.format(
                                etl_mapping.source_name,
                                scheduled_death
                            ),
                            console=True
                        )
                        break

                    source_value = etl_mapping.get_target_value(scheduled_death, cast=True, transform=True)
                    record[etl_mapping.target_name] = source_value
                    if etl_mapping.is_primary_key:
                        label_fields.append(source_value)

                record['label'] = ':'.join(label_fields)
                va_preload_data.append(record)
                self.result.add_exported_model(scheduled_death, console=self.verbose)

            if self.out_dir:
                self._save_entity_list_exported_json(va_preload_data)

            try:
                self.odk_client.entities.merge(
                    data=va_preload_data,
                    project_id=self.odk_entity_list_exporter.odk_entity_list.odk_project.project_id,
                    entity_list_name=self.odk_entity_list_exporter.odk_entity_list.name,
                    update_matched=True,
                    add_new_properties=False,
                    delete_not_matched=True
                )
                self.result.add_exported_entity_list(self.odk_entity_list_exporter.odk_entity_list)
            except Exception as ex:
                self.result.error('Failed to upload to ODK', error=ex, console=True)
        except Exception as ex:
            self.result.error('Error executing {}.'.format(self.__class__.__name__), error=ex, console=True)
        return self.result

    def _save_entity_list_exported_json(self, data):
        Utils.ensure_dirs(self.out_dir)
        out_filename = os.path.join(self.out_dir,
                                    'entity-list-{}.json'.format(self.odk_entity_list_exporter.odk_entity_list.name))
        Utils.save_json(data, out_filename)
