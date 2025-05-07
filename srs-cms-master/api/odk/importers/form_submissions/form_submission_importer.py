from api.odk.importers.form_submissions.form_submission_importer_factory import FromSubmissionImporterFactory
from api.odk.importers.form_submissions.form_submission_import_result import FromSubmissionImportResult
from api.common import Utils
from api.models import OdkProject, OdkForm, OdkFormImporterJob
from api.odk import OdkConfig
from datetime import datetime, timedelta
from django.db import models


class FromSubmissionImporter:
    def __init__(self, odk_projects=None, odk_forms=None, importers=None, form_versions=None,
                 import_start_date=None, import_end_date=None, out_dir=None, verbose=False):
        self.odk_config = None
        self.client = None
        self.odk_projects = Utils.to_list(odk_projects)
        self.odk_forms = Utils.to_list(odk_forms)
        self.only_importers = Utils.to_list(importers)
        self.form_versions = Utils.to_list(form_versions)
        self.import_start_date = import_start_date
        self.import_end_date = import_end_date
        self.out_dir = Utils.expand_path(out_dir) if out_dir else None
        self.verbose = verbose is True
        self.result = FromSubmissionImportResult()
        self._importer_started_at = Utils.to_aware_datetime(datetime.now())

    def execute(self):
        try:
            self.result.info('Importing ODK Form Submissions...', console=True)
            self.odk_config = OdkConfig.from_env()
            self.client = self.odk_config.client()

            _importers = self.only_importers
            self.only_importers = []
            for importer in _importers:
                class_name = FromSubmissionImporterFactory.get_importer_class_name(importer)
                if class_name is None:
                    self.result.error('Invalid Form Submission Importer: {}'.format(importer), console=True)
                else:
                    self.only_importers.append(class_name)

            if not self.result.errors:
                if not self.odk_projects and not self.odk_forms:
                    self.odk_projects = list(OdkProject.filter_by(is_enabled=True).values_list('id', flat=True))

                if self.odk_projects:
                    for odk_project in self.odk_projects:
                        self._import_project(odk_project)

                if self.odk_forms:
                    for odk_form in self.odk_forms:
                        if self.form_versions:
                            odk_form = odk_form if isinstance(odk_form, OdkForm) else OdkForm.find_by(id=odk_form)
                            if odk_form.version not in self.form_versions:
                                continue
                        self._import_form(odk_form)

        except Exception as ex:
            self.result.error('Error Executing ODK Form Submission Importer.', error=ex, console=True)
        finally:
            self._show_import_stats()
            return self.result

    def _show_import_stats(self):
        self.result.info("", console=True)

        if self.result.errors:
            self.result.info('Form Submission import completed with errors.', console=True)
            for error in self.result.errors:
                self.result.info(error, console=True)
        else:
            self.result.info('Form Submission import completed successfully.', console=True)

        imported_model_stats = {}
        total_model_stats = {}
        for imported_model in self.result.imported_models:
            class_name = imported_model.__class__.__name__
            if class_name not in imported_model_stats:
                imported_model_stats[class_name] = 0
            imported_model_stats[class_name] += 1

            if class_name not in total_model_stats:
                total_model_stats[class_name] = imported_model.__class__.objects.count()

        self.result.info("", console=True)
        self.result.info('Total Imported Form Submissions: {}'.format(len(self.result.imported_forms)), console=True)
        self.result.info('Total Imported Models: {}'.format(len(self.result.imported_models)), console=True)
        for class_name, count in imported_model_stats.items():
            self.result.info(
                ' - {}: Added: {} (Total: {})'.format(class_name, count, total_model_stats[class_name]),
                console=True)
        self.result.info('Imported Data Records: {}'.format(len(self.result.imported_data)), console=True)

    def _import_project(self, odk_project):
        odk_project = odk_project if isinstance(odk_project, OdkProject) else OdkProject.find_by(id=odk_project)

        if not odk_project:
            self.result.error('ODK Project ID not found: {}'.format(odk_project), console=True)
        elif odk_project and not odk_project.is_enabled:
            self.result.error('ODK Project not enabled: {}'.format(odk_project), console=True)
        elif odk_project:
            self.result.info(
                'Importing ODK Form Submissions for Project: {} (id: {})'.format(odk_project.name, odk_project.id),
                console=True)
            if self.form_versions:
                odk_form_ids = odk_project.odk_forms.filter(is_enabled=True,
                                                            version__in=self.form_versions).values_list('id', flat=True)
            else:
                odk_form_ids = odk_project.odk_forms.filter(is_enabled=True).values_list('id', flat=True)

            for odk_form_id in odk_form_ids:
                self._import_form(odk_form_id)

    def _import_form(self, odk_form):
        odk_form = odk_form if isinstance(odk_form, OdkForm) else OdkForm.find_by(id=odk_form)
        odk_project = odk_form.odk_project

        if not odk_project or not odk_form:
            if not odk_project:
                self.result.error('OdkProject not found: {}'.format(odk_project), console=True)
            if not odk_form:
                self.result.error('OdkForm not found: {}'.format(odk_form), console=True)
        elif odk_project and (not odk_project.is_enabled or not odk_form.is_enabled):
            if not odk_project.is_enabled:
                self.result.error('OdkProject not enabled: {} (id: {})'.format(odk_project.name, odk_project.id),
                                  console=True)
            if not odk_form.is_enabled:
                self.result.error('OdkForm not not enabled: {} (id: {})'.format(odk_form.name, odk_form.id),
                                  console=True)
        else:
            self.result.info(
                'Importing OdkForm: {} (id: {}, version: {}) '.format(odk_form.name, odk_form.id, odk_form.version),
                console=True)

            if self.only_importers:
                importers = odk_form.get_odk_form_importers(importers=self.only_importers)
            else:
                importers = odk_form.get_odk_form_importers()

            primary_odk_form_importer = odk_form.get_primary_odk_form_importer(_importer_list=importers)
            child_odk_form_importers = odk_form.get_child_odk_form_importers(_importer_list=importers)

            if primary_odk_form_importer is None:
                if self.only_importers:
                    self.result.info(
                        'OdkForm: {} (id: {}) does not have importer(s): {}. Skipping.'.format(
                            odk_form.name,
                            odk_form.id,
                            ','.join(self.only_importers)),
                        console=self.verbose)
                else:
                    self.result.error(
                        'Primary Importer not found for OdkForm: {} (id: {})'.format(odk_form.anme, odk_form.id),
                        console=True)
            else:
                self.result.info("")
                self.result.info(
                    'Executing Primary Form Submission Importer: {}'.format(primary_odk_form_importer.importer),
                    console=self.verbose)

                odk_form_importer_job = self._create_odk_form_importer_job(primary_odk_form_importer)

                self.result.info('Importing Form Submission Dates: {} - {}'.format(
                    odk_form_importer_job.import_start_date, odk_form_importer_job.import_end_date
                ), console=self.verbose)

                try:
                    primary_importer = FromSubmissionImporterFactory.get_importer(
                        primary_odk_form_importer,
                        odk_form,
                        primary_odk_form_importer,
                        child_importers=child_odk_form_importers,
                        import_start_date=odk_form_importer_job.import_start_date,
                        import_end_date=odk_form_importer_job.import_end_date,
                        out_dir=self.out_dir,
                        verbose=self.verbose
                    )
                    importer_result = primary_importer.execute()
                    self.result.merge(importer_result)
                except Exception as ex:
                    self.result.error('Error executing Form Submission importer.', error=ex, console=True)
                finally:
                    if self.result.errors:
                        odk_form_importer_job.status = OdkFormImporterJob.STATUS_ERRORED
                    else:
                        odk_form_importer_job.status = OdkFormImporterJob.STATUS_SUCCESSFUL
                    odk_form_importer_job.result = self.result.as_json()
                    odk_form_importer_job.save()
                return importer_result
        return None

    def _create_odk_form_importer_job(self, odk_form_importer):
        import_start_date = Utils.to_aware_datetime(self.import_start_date) if self.import_start_date else None
        import_end_date = Utils.to_aware_datetime(self.import_end_date) if self.import_end_date else None
        if import_start_date is None:
            import_start_date = (odk_form_importer.odk_form_importer_jobs
                                 .filter(status=OdkFormImporterJob.STATUS_SUCCESSFUL)
                                 .order_by('-import_end_date')
                                 .values_list('import_end_date', flat=True).first())
            if import_start_date:
                import_start_date = import_start_date + timedelta(seconds=1)
            else:
                import_start_date = Utils.to_aware_datetime(datetime.min)

        if import_end_date is None:
            import_end_date = self._importer_started_at

        if import_start_date > self._importer_started_at:
            import_start_date = self._importer_started_at

        if import_end_date > self._importer_started_at:
            import_end_date = self._importer_started_at

        if import_end_date < import_start_date:
            import_end_date = import_start_date

        odk_form_importer_job = odk_form_importer.odk_form_importer_jobs.create(
            odk_form_importer=odk_form_importer,
            status=OdkFormImporterJob.STATUS_RUNNING,
            import_start_date=import_start_date,
            import_end_date=import_end_date,
            args={
                "odk_projects": [p.id if isinstance(p, models.Model) else p for p in self.odk_projects],
                "odk_forms": [f.id if isinstance(f, models.Model) else f for f in self.odk_forms],
                "importers": self.only_importers,
                "form_version": odk_form_importer.odk_form.version,
                "import_start_date_orig": str(self.import_start_date) if self.import_start_date else None,
                "import_end_date_orig": str(self.import_end_date) if self.import_end_date else None
            }
        )
        return odk_form_importer_job
