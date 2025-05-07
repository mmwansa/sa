import pytest
from api.odk.importers.form_submissions.household_members_importer import HouseholdMembersImporter
from api.odk.importers.form_submissions.form_submission_importer_factory import FromSubmissionImporterFactory
from tests.factories.factories import OdkProjectFactory, FormSubmissionFactory, ProvinceFactory
from api.models import Household, HouseholdMember

DEFAULT_FORM_SUBMISSION_COUNT = 3


@pytest.fixture
def setup(mock_get_table):
    def _m(form_submission_count=DEFAULT_FORM_SUBMISSION_COUNT, form_submissions=[]):
        ProvinceFactory(with_clusters=True,
                        with_clusters__with_areas=True,
                        with_clusters__with_staff=True)

        odk_project = OdkProjectFactory(with_forms=True, with_forms__importers=True, with_forms__with_etl=True)

        household_odk_form = odk_project.odk_forms.filter(name=OdkProjectFactory.ODK_FORM_NAME_FOR_HOUSEHOLDS).first()
        household_odk_form_importer = household_odk_form.get_odk_form_importer(
            importer=FromSubmissionImporterFactory.ODK_HOUSEHOLDS_IMPORTER_NAME
        )
        household_etl_document = household_odk_form_importer.etl_document

        member_odk_form_importer = household_odk_form.get_odk_form_importer(
            importer=FromSubmissionImporterFactory.ODK_HOUSEHOLD_MEMBERS_IMPORTER_NAME
        )
        member_etl_document = member_odk_form_importer.etl_document

        household_form_submissions = form_submissions or []
        for _ in range(form_submission_count):
            household_form_submissions.append(
                FormSubmissionFactory.create_household(household_etl_document, for_member=member_etl_document)
            )

        mock_get_table(household_form_submissions)
        return household_odk_form, member_odk_form_importer, household_form_submissions

    yield _m


@pytest.mark.django_db
def test_it_imports_household_members(setup, expect_odk_form_submission_import_result):
    odk_form, odk_form_importer, event_form_submissions = setup()

    importer = HouseholdMembersImporter(odk_form, odk_form_importer)
    result = importer.execute()
    imported_households = list(filter(lambda e: isinstance(e, Household), result.imported_models))
    imported_members = list(filter(lambda e: isinstance(e, HouseholdMember), result.imported_models))
    assert len(imported_households) == 3
    assert len(imported_members) == 3
    expect_odk_form_submission_import_result(result, imported_models_count=DEFAULT_FORM_SUBMISSION_COUNT * 2)
    for index, imported_member in enumerate(imported_members):
        imported_household = imported_households[index]
        assert isinstance(imported_member, HouseholdMember)
        assert isinstance(imported_household, Household)
        assert imported_member.household == imported_household


@pytest.mark.django_db
def test_it_does_not_import_duplicate_household_members(setup, expect_odk_form_submission_import_result):
    odk_form, odk_form_importer, event_form_submissions = setup()

    importer = HouseholdMembersImporter(odk_form, odk_form_importer)
    result = importer.execute()
    expect_odk_form_submission_import_result(result, imported_models_count=DEFAULT_FORM_SUBMISSION_COUNT * 2)

    # Import the same records again
    importer = HouseholdMembersImporter(odk_form, odk_form_importer)
    result = importer.execute()
    expect_odk_form_submission_import_result(result, imported_models_count=0)
