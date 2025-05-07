import pytest
from .factories import FormSubmissionFactory, ProvinceFactory, OdkProjectFactory
from api.models import EtlDocument
from api.odk.importers.form_submissions.form_submission_importer_factory import FromSubmissionImporterFactory


@pytest.mark.django_db
def test_it_creates_odk_projects_and_etl():
    all_importer_names = list(map(lambda o: o[1], FromSubmissionImporterFactory.ODK_IMPORTERS))

    for importer_names in [all_importer_names, True]:
        odk_project = OdkProjectFactory(with_forms=True,
                                        with_forms__importers=importer_names,
                                        with_forms__with_etl=True)
        assert odk_project
        assert len(odk_project.odk_forms.all()) == 3
        for odk_form in odk_project.odk_forms.all():
            assert odk_form.name in [OdkProjectFactory.ODK_FORM_NAME_FOR_EVENTS,
                                     OdkProjectFactory.ODK_FORM_NAME_FOR_HOUSEHOLDS,
                                     OdkProjectFactory.ODK_FORM_NAME_FOR_VERBAL_AUTOPSIES]
            for odk_form_importer in odk_form.odk_form_importers.all():
                if isinstance(importer_names, list):
                    assert odk_form_importer.importer in all_importer_names
                etl_document = odk_form_importer.etl_document
                assert etl_document
                if isinstance(importer_names, list):
                    assert etl_document.name in importer_names
                assert len(etl_document.etl_mappings.all()) > 1


@pytest.mark.django_db
def test_creates_provinces():
    province = ProvinceFactory(with_clusters=3, with_clusters__with_areas=3, with_clusters__with_staff=3)
    assert province


@pytest.mark.django_db
def test_it_creates_events():
    OdkProjectFactory(with_forms=True, with_forms__importers=True, with_forms__with_etl=True)
    etl_doc = EtlDocument.objects.filter(name=FromSubmissionImporterFactory.ODK_EVENTS_IMPORTER_NAME).first()
    obj = FormSubmissionFactory.create_event(etl_doc, formVersion="1")
    assert obj is not None


@pytest.mark.django_db
def test_it_creates_death_events():
    OdkProjectFactory(with_forms=True, with_forms__importers=True, with_forms__with_etl=True)
    etl_doc = EtlDocument.objects.filter(name=FromSubmissionImporterFactory.ODK_EVENTS_IMPORTER_NAME).first()
    death_etl_doc = EtlDocument.objects.filter(name=FromSubmissionImporterFactory.ODK_DEATHS_IMPORTER_NAME).first()
    obj = FormSubmissionFactory.create_event(etl_doc, for_death=death_etl_doc, formVersion="1")
    assert obj is not None
