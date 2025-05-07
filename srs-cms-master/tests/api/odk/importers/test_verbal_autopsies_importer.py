import pytest
from api.odk.importers.form_submissions.verbal_autopsies_importer import VerbalAutopsiesImporter
from api.odk.importers.form_submissions.form_submission_importer_factory import FromSubmissionImporterFactory
from api.models import VerbalAutopsy
from tests.factories.factories import (OdkProjectFactory, FormSubmissionFactory, ProvinceFactory, DeathFactory)

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

        va_odk_form = odk_project.odk_forms.filter(name=OdkProjectFactory.ODK_FORM_NAME_FOR_VERBAL_AUTOPSIES).first()
        va_odk_form_importer = va_odk_form.get_odk_form_importer(
            importer=FromSubmissionImporterFactory.ODK_VERBALAUTOPSY_IMPORTER_NAME
        )
        va_etl_document = va_odk_form_importer.etl_document

        deaths = DeathFactory.create_batch(form_submission_count)

        va_form_submissions = form_submissions or []
        for index in range(form_submission_count):
            death = deaths[index]

            va_form_submissions.append(
                FormSubmissionFactory.create_verbal_autopsy(va_etl_document, death)
            )

        mock_get_table(va_form_submissions)
        return va_odk_form, va_odk_form_importer, va_form_submissions

    yield _m


@pytest.mark.django_db
def test_it_imports_verbal_autopsies(setup, expect_odk_form_submission_import_result):
    odk_form, odk_form_importer, event_form_submissions = setup()

    importer = VerbalAutopsiesImporter(odk_form, odk_form_importer)
    result = importer.execute()
    expect_odk_form_submission_import_result(result, imported_models_count=DEFAULT_FORM_SUBMISSION_COUNT)

    imported_va = result.imported_models[0]
    assert isinstance(imported_va, VerbalAutopsy)
    actual_model = VerbalAutopsy.objects.get(id=imported_va.id)
    assert actual_model == imported_va
    # assert actual_model.death == imported_death


@pytest.mark.django_db
def test_it_does_not_import_duplicate_verbal_autopsies(setup, expect_odk_form_submission_import_result):
    odk_form, odk_form_importer, event_form_submissions = setup()

    importer = VerbalAutopsiesImporter(odk_form, odk_form_importer)
    result = importer.execute()
    expect_odk_form_submission_import_result(result, imported_models_count=DEFAULT_FORM_SUBMISSION_COUNT)

    importer = VerbalAutopsiesImporter(odk_form, odk_form_importer)
    result = importer.execute()
    expect_odk_form_submission_import_result(result, imported_models_count=0)
