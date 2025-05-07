from api.odk.importers.form_submissions.form_submission_importer_base import FromSubmissionImporterBase
from api.odk.importers.form_submissions.form_submission_importer_factory import FromSubmissionImporterFactory
from api.models import Event, Death
from config.env import Env


class DeathsImporter(FromSubmissionImporterBase):
    def __init__(self, odk_form, odk_form_importer, **kwargs):
        super().__init__(odk_form, odk_form_importer, **kwargs)

    def execute(self):
        try:
            if self.validate_before_execute():
                self.import_submissions(Death)
        except Exception as ex:
            self.result.error('Error executing {}.'.format(self.__class__.__name__), error=ex, console=True)
        return self.result

    def on_can_import(self, etl_record, form_submission):
        try:
            event = self.get_model_or_try_execute_importer(Event,
                                                           FromSubmissionImporterFactory.ODK_EVENTS_IMPORTER_NAME,
                                                           form_submission)
            can_import = False
            if event is not None:
                if event.event_type == Event.EventType.DEATH:
                    can_import = True
                elif event.event_type == event.EventType.PREGNANCY_OUTCOME:
                    if ((event.birth_multi_still or 0) >= 1 or
                            event.birth_sing_outcome == Event.BirthOutcomeType.STILLBIRTH):
                        can_import = True

            return can_import
        except Exception as ex:
            self.result.error('Error executing {}.on_can_import:'.format(self.__class__.__name__),
                              error=ex, console=True)
            return False

    def on_before_save_model(self, new_death, etl_record, form_submission):
        use_existing_if_missing = Env.get("DEV_ODK_IMPORT_USE_EXISTING_IF_MISSING", cast=bool)
        try:
            event_key = self.get_key_from_record(form_submission)
            event = (Event.find_by(key=event_key) or
                     (Event.objects.first() if use_existing_if_missing else None))

            errors = []
            if event is None:
                errors.append(f"Event not found: {event_key or "NULL"}")

            if not errors:
                # TODO: do we need to set the death_type here? Where does death_type map from? See TODO in ETL.
                new_death.event = event
                new_death.death_status = Death.DeathStatus.NEW_DEATH
                return new_death.save_with_death_code()
            else:
                self.result.error(f"{new_death.key}, " + ", ".join(errors))
                return False
        except Exception as ex:
            self.result.error('Error executing {}.on_before_save_model.'.format(self.__class__.__name__),
                              error=ex, console=True)
            return False
