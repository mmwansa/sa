import os
import tempfile
import toml
from pyodk.client import Client
from django.conf import settings


class OdkConfig:
    def __init__(self, base_url=None, username=None, password=None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self._config_file_path = None

    def client(self, **kwargs):
        self._delete_pyodk_config()
        try:
            self._config_file_path = self.to_pyodk_config()
            client = Client(config_path=self._config_file_path, **kwargs)
        finally:
            self._delete_pyodk_config()
        return client

    def to_pyodk_config(self):
        config_toml = {
            "central": {
                "base_url": self.base_url,
                "username": self.username,
                "password": self.password
            }
        }
        # pyodk can only read from a config file, so we have to do this.
        # TODO: Try to make this work without needing to write files.
        with tempfile.NamedTemporaryFile(mode='w', delete=False, prefix='.pyodk_config', suffix='.toml') as temp_file:
            config_file_path = temp_file.name
            toml.dump(config_toml, temp_file)
            return config_file_path

    def _delete_pyodk_config(self):
        if self._config_file_path and os.path.exists(self._config_file_path):
            os.remove(self._config_file_path)

    @classmethod
    def from_env(cls):
        return OdkConfig(
            base_url=settings.ODK_BASE_URL,
            username=settings.ODK_USERNAME,
            password=settings.ODK_PASSWORD
        )
