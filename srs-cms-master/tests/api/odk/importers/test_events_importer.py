import pytest
from api.odk.importers.form_submissions.events_importer import EventsImporter
from api.odk.importers.form_submissions.form_submission_importer_factory import FromSubmissionImporterFactory
from api.models import Event
from tests.factories.factories import OdkProjectFactory, FormSubmissionFactory, ProvinceFactory

DEFAULT_FORM_SUBMISSION_COUNT = 3


@pytest.fixture
def setup(mock_get_table):
    def _m(form_submission_count=DEFAULT_FORM_SUBMISSION_COUNT, form_submissions=[]):
        ProvinceFactory(with_clusters=True,
                        with_clusters__with_areas=True,
                        with_clusters__with_staff=True)

        odk_project = OdkProjectFactory(with_forms=True,
                                        with_forms__importers=True,
                                        with_forms__with_etl=True)

        event_odk_form = odk_project.odk_forms.filter(name=OdkProjectFactory.ODK_FORM_NAME_FOR_EVENTS).first()
        event_odk_form_importer = event_odk_form.get_odk_form_importer(
            importer=FromSubmissionImporterFactory.ODK_EVENTS_IMPORTER_NAME
        )
        event_etl_document = event_odk_form_importer.etl_document

        event_form_submissions = form_submissions or []
        for _ in range(form_submission_count):
            event_form_submissions.append(
                FormSubmissionFactory.create_event(event_etl_document)
            )

        mock_get_table(event_form_submissions)
        return event_odk_form, event_odk_form_importer, event_form_submissions

    yield _m


@pytest.mark.django_db
def test_it_imports_events(setup, expect_odk_form_submission_import_result):
    odk_form, odk_form_importer, event_form_submissions = setup()

    importer = EventsImporter(odk_form, odk_form_importer)
    result = importer.execute()
    expect_odk_form_submission_import_result(result, imported_models_count=DEFAULT_FORM_SUBMISSION_COUNT)

    for imported_event in result.imported_models:
        assert isinstance(imported_event, Event)
        actual_model = Event.objects.get(id=imported_event.id)
        assert actual_model == imported_event


@pytest.mark.django_db
def test_it_does_not_import_duplicate_events(setup, expect_odk_form_submission_import_result):
    odk_form, odk_form_importer, event_form_submissions = setup()

    importer = EventsImporter(odk_form, odk_form_importer)
    result = importer.execute()
    expect_odk_form_submission_import_result(result, imported_models_count=DEFAULT_FORM_SUBMISSION_COUNT)

    # Import the same records again
    importer = EventsImporter(odk_form, odk_form_importer)
    result = importer.execute()
    expect_odk_form_submission_import_result(result, imported_models_count=0)
