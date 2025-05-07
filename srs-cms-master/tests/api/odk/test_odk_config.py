import pytest
import os
from api.odk.odk_config import OdkConfig


def test_it_deletes_the_config_temp_file(settings):
    settings.ODK_BASE_URL = "https://odk.example.com"
    settings.ODK_USERNAME = "test_user"
    settings.ODK_PASSWORD = "test_password"
    odk_config = OdkConfig.from_env()
    assert odk_config._config_file_path is None
    assert odk_config.base_url == settings.ODK_BASE_URL
    assert odk_config.username == settings.ODK_USERNAME
    assert odk_config.password == settings.ODK_PASSWORD

    odk_client = odk_config.client()
    assert odk_client
    assert odk_config._config_file_path is not None
    assert os.path.exists(odk_config._config_file_path) is False

    # Creates and deletes the file when client() is called.
    last_config_file_path = odk_config._config_file_path
    odk_client = odk_config.client()
    assert odk_config._config_file_path != last_config_file_path
    assert os.path.exists(odk_config._config_file_path) is False


def test_integration():
    odk_config = OdkConfig.from_env()
    with odk_config.client() as odk_client:
        # Opening the client will make a request and authenticate the session.
        # ENV Vars must be configured for this to work.
        assert odk_client.open()
