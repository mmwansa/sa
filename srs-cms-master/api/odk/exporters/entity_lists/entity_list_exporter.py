from api.common import Utils
from api.models import OdkProject, OdkEntityList, OdkEntityListExporterJob
from api.odk import OdkConfig
from api.odk.exporters.entity_lists.entity_list_exporter_factory import EntityListExporterFactory
from api.odk.exporters.entity_lists.entity_list_export_result import EntityListExportResult
from datetime import datetime
from django.db import models


class EntityListExporter:
    def __init__(self, odk_projects=None, odk_entity_lists=None, exporters=None, out_dir=None, verbose=False):
        self.odk_config = None
        self.client = None
        self.odk_projects = Utils.to_list(odk_projects)
        self.odk_entity_lists = Utils.to_list(odk_entity_lists)
        self.only_exporters = Utils.to_list(exporters)
        self.out_dir = Utils.expand_path(out_dir) if out_dir else None
        self.verbose = verbose is True
        self.result = EntityListExportResult()
        self._exporter_started_at = Utils.to_aware_datetime(datetime.now())

    def execute(self):
        try:
            self.result.info('Exporting ODK Entity Lists...', console=True)
            self.odk_config = OdkConfig.from_env()
            self.client = self.odk_config.client()

            _exporters = self.only_exporters
            self.only_exporters = []
            for exporter in _exporters:
                class_name = EntityListExporterFactory.get_exporter_class_name(exporter)
                if class_name is None:
                    self.result.error('Invalid Entity List Exporter: {}'.format(exporter), console=True)
                else:
                    self.only_exporters.append(class_name)

            if not self.result.errors:
                if not self.odk_projects and not self.odk_entity_lists:
                    self.odk_projects = list(OdkProject.filter_by(is_enabled=True).values_list('id', flat=True))

                if self.odk_projects:
                    for odk_project in self.odk_projects:
                        self._export_project(odk_project)

                if self.odk_entity_lists:
                    for odk_entity_list in self.odk_entity_lists:
                        self._export_entity_list(odk_entity_list)

        except Exception as ex:
            self.result.error('Error Executing ODK Entity List Exporter.', error=ex, console=True)
        finally:
            self._show_export_stats()
            return self.result

    def _show_export_stats(self):
        self.result.info("", console=True)

        if self.result.errors:
            self.result.info('Entity List export completed with errors.', console=True)
            for error in self.result.errors:
                self.result.info(error, console=True)
        else:
            self.result.info('Entity List export completed successfully.', console=True)

        exported_model_stats = {}
        for exported_model in self.result.exported_models:
            class_name = exported_model.__class__.__name__
            if class_name not in exported_model_stats:
                exported_model_stats[class_name] = 0
            exported_model_stats[class_name] += 1

        self.result.info("", console=True)
        self.result.info('Total Exported Entity Lists: {}'.format(len(self.result.exported_entity_lists)), console=True)
        self.result.info('Total Exported Models: {}'.format(len(self.result.exported_models)), console=True)
        for class_name, count in exported_model_stats.items():
            self.result.info(' - {}: Exported: {}'.format(class_name, count), console=True)

    def _export_project(self, odk_project):
        odk_project = odk_project if isinstance(odk_project, OdkProject) else OdkProject.find_by(id=odk_project)

        if not odk_project:
            self.result.error('OdkProject ID not found: {}'.format(odk_project), console=True)
        elif odk_project and not odk_project.is_enabled:
            self.result.error('OdkProject not enabled: {}'.format(odk_project), console=True)
        elif odk_project:
            self.result.info(
                'Exporting ODK Entity Lists for Project: {} (id: {})'.format(odk_project.name, odk_project.id),
                console=True)

            odk_entity_lists_ids = odk_project.odk_entity_lists.filter(is_enabled=True).values_list('id', flat=True)

            for odk_entity_lists_id in odk_entity_lists_ids:
                self._export_entity_list(odk_entity_lists_id)

    def _export_entity_list(self, odk_entity_list):
        odk_entity_list = odk_entity_list if isinstance(odk_entity_list, OdkEntityList) else OdkEntityList.find_by(
            id=odk_entity_list)
        odk_project = odk_entity_list.odk_project

        if not odk_project or not odk_entity_list:
            if not odk_project:
                self.result.error('OdkProject not found: {}'.format(odk_project), console=True)
            if not odk_entity_list:
                self.result.error('OdkEntity List not found: {}'.format(odk_entity_list), console=True)
        elif odk_project and (not odk_project.is_enabled or not odk_entity_list.is_enabled):
            if not odk_project.is_enabled:
                self.result.error('OdkProject not enabled: {} (id: {})'.format(odk_project.name, odk_project.id),
                                  console=True)
            if not odk_entity_list.is_enabled:
                self.result.error(
                    'OdkEntityList not not enabled: {} (id: {})'.format(odk_entity_list.name, odk_entity_list.id),
                    console=True)
        else:
            self.result.info(
                'Exporting OdkEntityList: {} (id: {}) '.format(odk_entity_list.name, odk_entity_list.id),
                console=True)

            if self.only_exporters:
                odk_entity_list_exporters = odk_entity_list.get_odk_entity_list_exporters(exporters=self.only_exporters)
            else:
                odk_entity_list_exporters = odk_entity_list.get_odk_entity_list_exporters()

            if not odk_entity_list_exporters:
                if self.only_exporters:
                    self.result.info(
                        'OdkEntityList: {} (id: {}) does not have exporter(s): {}. Skipping.'.format(
                            odk_entity_list.name,
                            odk_entity_list.id,
                            ','.join(self.only_exporters)),
                        console=self.verbose)
                else:
                    self.result.error(
                        'Exporters not found for OdkEntityList: {} (id: {})'.format(odk_entity_list.name,
                                                                                    odk_entity_list.id),
                        console=True)
            else:
                for odk_entity_list_exporter in odk_entity_list_exporters:
                    self.result.info("")
                    self.result.info(
                        'Executing Entity List Exporter: {}'.format(odk_entity_list_exporter.exporter),
                        console=self.verbose)

                    odk_entity_list_exporter_job = odk_entity_list_exporter.odk_entity_list_exporter_jobs.create(
                        export_date=Utils.to_aware_datetime(datetime.now()),
                        status=OdkEntityListExporterJob.STATUS_RUNNING,
                        args={
                            "odk_projects": [p.id if isinstance(p, models.Model) else p for p in self.odk_projects],
                            "odk_entity_lists": [f.id if isinstance(f, models.Model) else f for f in
                                                 self.odk_entity_lists],
                            "exporters": self.only_exporters
                        }
                    )
                    try:
                        exporter = EntityListExporterFactory.get_exporter(
                            odk_entity_list_exporter,
                            odk_entity_list_exporter,
                            out_dir=self.out_dir,
                            verbose=self.verbose
                        )
                        exporter_result = exporter.execute()
                        self.result.merge(exporter_result)
                    except Exception as ex:
                        self.result.error('Error executing Entity List exporter.', error=ex, console=True)
                    finally:
                        if self.result.errors:
                            odk_entity_list_exporter_job.status = OdkEntityListExporterJob.STATUS_ERRORED
                        else:
                            odk_entity_list_exporter_job.status = OdkEntityListExporterJob.STATUS_SUCCESSFUL
                        odk_entity_list_exporter_job.result = self.result.as_json()
                        odk_entity_list_exporter_job.save()
                return self.result
        return None
