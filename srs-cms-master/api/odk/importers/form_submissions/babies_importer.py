from api.odk.importers.form_submissions.form_submission_importer_base import FromSubmissionImporterBase
from api.odk.importers.form_submissions.form_submission_importer_factory import FromSubmissionImporterFactory
from api.models import Event, Baby
from config.env import Env


class BabiesImporter(FromSubmissionImporterBase):
    def __init__(self, odk_form, odk_form_importer, **kwargs):
        super().__init__(odk_form, odk_form_importer, **kwargs)

    def execute(self):
        try:
            if self.validate_before_execute():
                self.import_submissions(Baby)
        except Exception as ex:
            self.result.error('Error executing {}.'.format(self.__class__.__name__), error=ex, console=True)
        return self.result

    def on_can_import(self, etl_record, form_submission):
        try:
            event = self.get_model_or_try_execute_importer(Event,
                                                           FromSubmissionImporterFactory.ODK_EVENTS_IMPORTER_NAME,
                                                           form_submission)
            # TODO: is this the correct event_type?
            can_import = event is not None and event.event_type in [Event.EventType.PREGNANCY,
                                                                    Event.EventType.PREGNANCY_OUTCOME]
            return can_import
        except Exception as ex:
            self.result.error('Error executing {}.on_can_import:'.format(self.__class__.__name__),
                              error=ex, console=True)
            return False

    def on_before_save_model(self, new_baby, etl_record, form_submission):
        use_existing_if_missing = Env.get("DEV_ODK_IMPORT_USE_EXISTING_IF_MISSING", cast=bool)
        try:
            event_key = self.get_key_from_record(form_submission)
            event = (Event.find_by(key=event_key) or
                     (Event.objects.first() if use_existing_if_missing else None))

            errors = []
            if event is None:
                errors.append(f"Event not found: {event_key or "NULL"}")

            if not errors:
                new_baby.event = event
                return True
            else:
                self.result.error(f"{new_baby.key}, " + ", ".join(errors))
                return False
        except Exception as ex:
            self.result.error('Error executing {}.on_before_save_model.'.format(self.__class__.__name__),
                              error=ex, console=True)
            return False
