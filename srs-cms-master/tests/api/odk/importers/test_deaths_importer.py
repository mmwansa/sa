import pytest
from api.odk.importers.form_submissions.deaths_importer import DeathsImporter
from api.odk.importers.form_submissions.form_submission_importer_factory import FromSubmissionImporterFactory
from api.models import Event, Death
from tests.factories.factories import OdkProjectFactory, FormSubmissionFactory, ProvinceFactory

DEFAULT_FORM_SUBMISSION_COUNT = 3


@pytest.fixture
def setup(mock_get_table):
    def _m(form_submission_count=DEFAULT_FORM_SUBMISSION_COUNT, form_submissions=[]):
        ProvinceFactory(with_clusters=True,
                        with_clusters__with_areas=True,
                        with_clusters__with_staff=True)

        odk_project = OdkProjectFactory(with_forms=True, with_forms__importers=True, with_forms__with_etl=True)

        event_odk_form = odk_project.odk_forms.filter(name=OdkProjectFactory.ODK_FORM_NAME_FOR_EVENTS).first()
        event_odk_form_importer = event_odk_form.get_odk_form_importer(
            importer=FromSubmissionImporterFactory.ODK_EVENTS_IMPORTER_NAME
        )
        event_etl_document = event_odk_form_importer.etl_document

        death_odk_form_importer = event_odk_form.get_odk_form_importer(
            importer=FromSubmissionImporterFactory.ODK_DEATHS_IMPORTER_NAME
        )
        death_etl_document = death_odk_form_importer.etl_document

        event_form_submissions = form_submissions or []
        for _ in range(form_submission_count):
            event_form_submissions.append(
                FormSubmissionFactory.create_event(event_etl_document, for_death=death_etl_document)
            )

        mock_get_table(event_form_submissions)
        return event_odk_form, death_odk_form_importer, event_form_submissions

    yield _m


@pytest.mark.django_db
def test_it_imports_deaths(setup, expect_odk_form_submission_import_result):
    odk_form, odk_form_importer, event_form_submissions = setup()

    importer = DeathsImporter(odk_form, odk_form_importer)
    result = importer.execute()
    imported_events = list(filter(lambda e: isinstance(e, Event), result.imported_models))
    imported_deaths = list(filter(lambda e: isinstance(e, Death), result.imported_models))
    assert len(imported_events) == 3
    assert len(imported_deaths) == 3
    expect_odk_form_submission_import_result(result, imported_models_count=DEFAULT_FORM_SUBMISSION_COUNT * 2)
    for index, imported_death in enumerate(imported_deaths):
        imported_event = imported_events[index]
        assert isinstance(imported_death, Death)
        assert isinstance(imported_event, Event)
        assert imported_death.event == imported_event


@pytest.mark.django_db
def test_it_does_not_import_duplicate_deaths(setup, expect_odk_form_submission_import_result):
    odk_form, odk_form_importer, event_form_submissions = setup()

    odk_form_importer = odk_form.get_odk_form_importer(importer=FromSubmissionImporterFactory.ODK_DEATHS_IMPORTER_NAME)
    importer = DeathsImporter(odk_form, odk_form_importer)
    result = importer.execute()
    expect_odk_form_submission_import_result(result, imported_models_count=DEFAULT_FORM_SUBMISSION_COUNT * 2)

    # Import the same records again
    importer = DeathsImporter(odk_form, odk_form_importer)
    result = importer.execute()
    expect_odk_form_submission_import_result(result, imported_models_count=0)
