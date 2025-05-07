import pytest
from api.dev.seeds.seed_loader import SeedLoader
from api.models import OdkProject


@pytest.fixture(autouse=True)
def auto_set_env(monkeypatch):
    # Disable this setting for all tests.
    monkeypatch.setenv('DEV_ODK_IMPORT_USE_EXISTING_IF_MISSING', 'False')


@pytest.fixture(scope="session")
def seed_loader():
    yield SeedLoader('test')


@pytest.fixture()
def mock_odk_login(mocker):
    """Mocks the pyodk session to always return logged in."""
    mock_client = mocker.patch("pyodk.client.Client.open")
    mock_client.return_value = True
    yield mock_client


@pytest.fixture
def expect_odk_form_submission_import_result():
    """Checks the form submission import result."""

    def _m(odk_import_result, imported_forms_count=None, imported_models_count=None,
           imported_data_count=None, error_count=0, form_version=None, imported_model_types=None):
        if imported_forms_count is not None:
            assert len(odk_import_result.imported_forms) == imported_forms_count

        if imported_models_count is not None:
            assert len(odk_import_result.imported_models) == imported_models_count

        if imported_data_count is not None:
            assert len(odk_import_result.imported_data) == imported_data_count

        if error_count is not None:
            assert len(odk_import_result.errors) == error_count, 'Errors: {}'.format(odk_import_result.errors)

        if form_version:
            for imported_form in odk_import_result.imported_data:
                assert imported_form['__system']['formVersion'] == form_version

        if imported_model_types:
            expected_model_types = imported_model_types
            for imported_model in odk_import_result.imported_models:
                klass = imported_model.__class__
                if klass in expected_model_types:
                    expected_model_types.remove(klass)
            assert len(expected_model_types) == 0, \
                f"Imported model types not imported: {', '.join(map(str, expected_model_types))}"

    yield _m


@pytest.fixture
def mock_get_table(mocker):
    """Mocks the pyodk submissions.get_table method."""

    def _m(mocked_form_submissions=[]):
        mock_client = mocker.patch("pyodk._endpoints.submissions.SubmissionService.get_table")
        mock_client.return_value = {
            "value": mocked_form_submissions
        }
        return mock_client

    yield _m


@pytest.fixture
def mock_get_table_dynamic(mocker, seed_loader):
    """Mocks the pyodk submissions.get_table method and returns the correct form submissions."""

    def _m(events=[], deaths=[], babies=[], households=[], household_members=[], verbal_autopsies=[]):
        def mocked_get_table(*args, form_id=None, project_id=None, **kwargs):
            odk_project = OdkProject.objects.get(project_id=project_id)
            odk_form = odk_project.odk_forms.get(xml_form_id=form_id)
            value = []
            if odk_form.name == "Events":
                value = events + deaths + babies
            elif odk_form.name == "Households":
                value = households + household_members
            elif odk_form.name == "Verbal Autopsies":
                value = verbal_autopsies
            return {"value": value}

        mock_client = mocker.patch("pyodk._endpoints.submissions.SubmissionService.get_table",
                                   side_effect=mocked_get_table)
        return mock_client

    yield _m
