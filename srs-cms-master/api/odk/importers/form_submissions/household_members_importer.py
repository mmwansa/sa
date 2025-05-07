from api.odk.importers.form_submissions.form_submission_importer_base import FromSubmissionImporterBase
from api.odk.importers.form_submissions.form_submission_importer_factory import FromSubmissionImporterFactory
from api.models import Household, HouseholdMember
from config.env import Env


class HouseholdMembersImporter(FromSubmissionImporterBase):
    def __init__(self, odk_form, odk_form_importer, **kwargs):
        super().__init__(odk_form, odk_form_importer, **kwargs)

    def execute(self):
        try:
            if self.validate_before_execute():
                self.import_submissions(HouseholdMember)
        except Exception as ex:
            self.result.error('Error executing {}.'.format(self.__class__.__name__), error=ex, console=True)
        return self.result

    def on_can_import(self, etl_record, form_submission):
        try:
            household = self.get_model_or_try_execute_importer(Household,
                                                               FromSubmissionImporterFactory.ODK_HOUSEHOLDS_IMPORTER_NAME,
                                                               form_submission)
            # TODO: what should the logic be here?
            can_import = household is not None
            return can_import
        except Exception as ex:
            self.result.error('Error executing {}.on_can_import:'.format(self.__class__.__name__),
                              error=ex, console=True)
            return False

    def on_before_save_model(self, new_household_member, etl_record, form_submission):
        use_existing_if_missing = Env.get("DEV_ODK_IMPORT_USE_EXISTING_IF_MISSING", cast=bool)
        try:
            household_key = self.get_key_from_record(form_submission)
            household = (Household.find_by(key=household_key) or
                         (Household.objects.first() if use_existing_if_missing else None))

            errors = []
            if household is None:
                errors.append(f"Household not found: {household_key or "NULL"}")

            if not errors:
                new_household_member.household = household
                return True
            else:
                self.result.error(f"{new_household_member.key}, " + ", ".join(errors))
                return False
        except Exception as ex:
            self.result.error('Error executing {}.on_before_save_model.'.format(self.__class__.__name__),
                              error=ex, console=True)
            return False
