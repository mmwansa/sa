import pytest
import os
import tempfile
from datetime import datetime
from api.models import OdkProject, Event, Death, Baby, Household, HouseholdMember, VerbalAutopsy
from api.odk.importers.form_submissions.form_submission_importer import FromSubmissionImporter
from api.odk.importers.form_submissions.form_submission_importer_factory import FromSubmissionImporterFactory
from tests.factories.factories import OdkProjectFactory, FormSubmissionFactory, ProvinceFactory, DeathFactory

DEFAULT_FORM_SUBMISSION_COUNT = 3


@pytest.fixture
def setup(mock_get_table_dynamic):
    def _m(form_submission_count=DEFAULT_FORM_SUBMISSION_COUNT):
        ProvinceFactory(with_clusters=True,
                        with_clusters__with_areas=True,
                        with_clusters__with_staff=True)

        odk_project = OdkProjectFactory(with_forms=True,
                                        with_forms__importers=True,
                                        with_forms__with_etl=True)

        ################################################################################################################
        # Events
        event_odk_form = odk_project.odk_forms.filter(name=OdkProjectFactory.ODK_FORM_NAME_FOR_EVENTS).first()
        event_odk_form_importer = event_odk_form.get_odk_form_importer(
            importer=FromSubmissionImporterFactory.ODK_EVENTS_IMPORTER_NAME
        )

        event_form_submissions = []
        for _ in range(form_submission_count):
            event_form_submissions.append(FormSubmissionFactory.create_event(event_odk_form_importer.etl_document))

        # Deaths
        death_odk_form_importer = event_odk_form.get_odk_form_importer(
            importer=FromSubmissionImporterFactory.ODK_DEATHS_IMPORTER_NAME
        )
        death_form_submissions = []
        for _ in range(form_submission_count):
            death_form_submissions.append(
                FormSubmissionFactory.create_event(event_odk_form_importer.etl_document,
                                                   for_death=death_odk_form_importer.etl_document)
            )

        # Babies
        baby_odk_form_importer = event_odk_form.get_odk_form_importer(
            importer=FromSubmissionImporterFactory.ODK_BABIES_IMPORTER_NAME
        )
        baby_form_submissions = []
        for _ in range(form_submission_count):
            baby_form_submissions.append(FormSubmissionFactory.create_event(event_odk_form_importer.etl_document,
                                                                            for_baby=baby_odk_form_importer.etl_document))

        ################################################################################################################
        # Households
        household_odk_form = odk_project.odk_forms.filter(name=OdkProjectFactory.ODK_FORM_NAME_FOR_HOUSEHOLDS).first()
        household_odk_form_importer = household_odk_form.get_odk_form_importer(
            importer=FromSubmissionImporterFactory.ODK_HOUSEHOLDS_IMPORTER_NAME
        )

        household_form_submissions = []
        for _ in range(form_submission_count):
            household_form_submissions.append(
                FormSubmissionFactory.create_household(household_odk_form_importer.etl_document)
            )

        # HouseholdMembers
        household_members_odk_form_importer = household_odk_form.get_odk_form_importer(
            importer=FromSubmissionImporterFactory.ODK_HOUSEHOLD_MEMBERS_IMPORTER_NAME
        )

        household_members_form_submissions = []
        for _ in range(form_submission_count):
            household_members_form_submissions.append(
                FormSubmissionFactory.create_household(household_odk_form_importer.etl_document,
                                                       for_member=household_members_odk_form_importer.etl_document)
            )

        ################################################################################################################
        # VerbalAutopsy
        va_odk_form = odk_project.odk_forms.filter(name=OdkProjectFactory.ODK_FORM_NAME_FOR_VERBAL_AUTOPSIES).first()
        va_odk_form_importer = va_odk_form.get_odk_form_importer(
            importer=FromSubmissionImporterFactory.ODK_VERBALAUTOPSY_IMPORTER_NAME
        )

        va_form_submissions = []
        deaths = DeathFactory.create_batch(form_submission_count)
        for index in range(form_submission_count):
            death = deaths[index]
            va_form_submissions.append(
                FormSubmissionFactory.create_verbal_autopsy(va_odk_form_importer.etl_document, death)
            )

        mock_get_table_dynamic(
            events=event_form_submissions,
            deaths=death_form_submissions,
            babies=baby_form_submissions,
            households=household_form_submissions,
            household_members=household_members_form_submissions,
            verbal_autopsies=va_form_submissions
        )
        return odk_project

    yield _m


@pytest.mark.django_db
def test_it_imports_all_projects_and_forms(setup, expect_odk_form_submission_import_result):
    setup()
    importer = FromSubmissionImporter()
    odk_import_result = importer.execute()
    expect_odk_form_submission_import_result(
        odk_import_result,
        error_count=0,
        imported_model_types=[Event, Death, Baby, Household, HouseholdMember, VerbalAutopsy]
    )


@pytest.mark.django_db
def test_it_imports_all_projects_and_forms_with_start_end_dates(setup, expect_odk_form_submission_import_result):
    setup()
    importer = FromSubmissionImporter(import_start_date=datetime.min, import_end_date=datetime.now())
    odk_import_result = importer.execute()
    expect_odk_form_submission_import_result(odk_import_result, error_count=0)

    # Uses the last end_date and should return 0 items imported.
    importer = FromSubmissionImporter()
    odk_import_result = importer.execute()
    expect_odk_form_submission_import_result(odk_import_result, error_count=0)


@pytest.mark.django_db
def test_it_does_not_reimport_all_projects_and_forms(setup, expect_odk_form_submission_import_result):
    setup()
    importer = FromSubmissionImporter(import_start_date=datetime.min, import_end_date=datetime.max)
    odk_import_result = importer.execute()
    expect_odk_form_submission_import_result(odk_import_result, error_count=0)

    importer = FromSubmissionImporter(import_start_date=datetime.min, import_end_date=datetime.max)
    odk_import_result = importer.execute()
    expect_odk_form_submission_import_result(odk_import_result, imported_models_count=0, imported_data_count=0,
                                             error_count=0)


@pytest.mark.django_db
def test_it_imports_all_projects_and_forms_and_saves_submissions(setup, expect_odk_form_submission_import_result):
    setup()
    out_dir = tempfile.mkdtemp()
    importer = FromSubmissionImporter(out_dir=out_dir)
    odk_import_result = importer.execute()
    expect_odk_form_submission_import_result(odk_import_result, error_count=0)
    for model in odk_import_result.imported_models:
        if hasattr(model, 'form_version'):
            expected_path = os.path.join(out_dir, 'form-submission-{}-{}-{}.json'.format(model.form_version,
                                                                                         model.__class__.__name__,
                                                                                         model.key))
            assert os.path.isfile(expected_path)

        if isinstance(model, Baby):
            expected_path = os.path.join(out_dir, 'form-submission-{}-{}-{}-{}.json'.format(model.event.form_version,
                                                                                            model.__class__.__name__,
                                                                                            model.event.key,
                                                                                            model.key))
            assert os.path.isfile(expected_path)
        elif isinstance(model, HouseholdMember):
            expected_path = os.path.join(out_dir,
                                         'form-submission-{}-{}-{}-{}.json'.format(model.household.form_version,
                                                                                   model.__class__.__name__,
                                                                                   model.household.key,
                                                                                   model.key))
            assert os.path.isfile(expected_path)


@pytest.mark.django_db
def test_it_imports_specific_projects_and_forms(setup, expect_odk_form_submission_import_result):
    setup()
    odk_project = OdkProject.objects.all().first()

    importer = FromSubmissionImporter(odk_projects=odk_project)
    odk_import_result = importer.execute()
    expect_odk_form_submission_import_result(odk_import_result, error_count=0)

    importer = FromSubmissionImporter(odk_forms=list(odk_project.odk_forms.all()))
    odk_import_result = importer.execute()
    expect_odk_form_submission_import_result(odk_import_result, error_count=0)


@pytest.mark.django_db
def test_it_imports_specific_form_versions(setup, expect_odk_form_submission_import_result):
    setup()
    odk_project = OdkProject.objects.all().first()
    odk_project_forms = list(odk_project.odk_forms.all())
    form_version = odk_project_forms[0].version
    importer = FromSubmissionImporter(odk_projects=odk_project, form_versions=[form_version])
    odk_import_result = importer.execute()
    expect_odk_form_submission_import_result(odk_import_result, error_count=0, form_version=form_version)

    form_version = odk_project_forms[-1].version
    importer = FromSubmissionImporter(odk_forms=odk_project_forms, form_versions=[form_version])
    odk_import_result = importer.execute()
    expect_odk_form_submission_import_result(odk_import_result, error_count=0, form_version=form_version)


@pytest.mark.django_db
def test_it_imports_specific_importers(setup, expect_odk_form_submission_import_result):
    setup()
    odk_project = OdkProject.objects.all().first()
    odk_project_forms = list(odk_project.odk_forms.all())

    # Importer full path.
    importers = FromSubmissionImporterFactory.ODK_DEATHS_IMPORTER_CLASS
    importer = FromSubmissionImporter(odk_projects=odk_project, importers=importers)
    odk_import_result = importer.execute()
    expect_odk_form_submission_import_result(odk_import_result, error_count=0)

    # Importer Name
    importers = FromSubmissionImporterFactory.ODK_HOUSEHOLDS_IMPORTER_NAME
    importer = FromSubmissionImporter(odk_forms=odk_project_forms, importers=importers)
    odk_import_result = importer.execute()
    expect_odk_form_submission_import_result(odk_import_result, error_count=0)
