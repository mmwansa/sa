from api.odk.importers.form_submissions.form_submission_importer_base import FromSubmissionImporterBase
from api.models import VerbalAutopsy, Cluster, Area, Death
from config.env import Env


class VerbalAutopsiesImporter(FromSubmissionImporterBase):
    def __init__(self, odk_form, odk_form_importer, **kwargs):
        super().__init__(odk_form, odk_form_importer, **kwargs)

    def execute(self):
        try:
            if self.validate_before_execute():
                self.import_submissions(VerbalAutopsy)
        except Exception as ex:
            self.result.error('Error executing {}.'.format(self.__class__.__name__), error=ex, console=True)
        return self.result

    def on_before_save_model(self, new_va, etl_record, form_submission):
        use_existing_if_missing = Env.get("DEV_ODK_IMPORT_USE_EXISTING_IF_MISSING", cast=bool)
        try:
            cluster = (Cluster.find_by(code=new_va.cluster_code) or
                       (Cluster.objects.first() if use_existing_if_missing else None))
            area = (Area.find_by(code=new_va.area_code) or
                    (Area.objects.first() if use_existing_if_missing else None))

            death = ((Death.find_by(death_code=new_va.death_code)) or
                     (
                         (Death.objects.filter(va_completed_date=None, death_code__istartswith=cluster.code).first() or
                          Death.objects.filter(va_completed_date=None).first()) if use_existing_if_missing else None)
                     )

            errors = []
            if cluster is None:
                errors.append(f"Cluster not found: {new_va.cluster_code or "NULL"}")
            if area is None:
                errors.append(f"Area not found: {new_va.area_code or "NULL"}")
            if death is None:
                errors.append(f"Death not found: {new_va.death_code or "NULL"}")

            if not errors:
                new_va.cluster = cluster
                new_va.area = area
                new_va.death = death
                new_va.save()

                death.set_va_completed()
                return True
            else:
                self.result.error(f"VerbalAutopsy: {new_va.key}, " + ", ".join(errors))
                return False
        except Exception as ex:
            self.result.error('Error executing {}.on_before_save_model.'.format(self.__class__.__name__),
                              error=ex, console=True)
            return False
