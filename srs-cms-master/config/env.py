import environ
import os
from pathlib import Path


class Env:
    _ENV = None

    @classmethod
    def _env(cls):
        if cls._ENV is None:
            cls._ENV = environ.Env(
                DEBUG=(bool, False),
                ALLOWED_HOSTS=(str, '')
            )
            base_dir = Path(__file__).resolve().parent.parent
            environ.Env.read_env(os.path.join(base_dir, '.env'), overwrite=True)
        return cls._ENV

    @classmethod
    def get(cls, name, **kwargs):
        return cls._env().get_value(name, **kwargs)

    @classmethod
    def secret_key(cls):
        return cls._env().str('SECRET_KEY')

    @classmethod
    def debug(cls):
        return cls._env().bool('DEBUG')

    @classmethod
    def log_level(cls):
        return cls._env().bool('LOG_LEVEL', 'INFO')

    @classmethod
    def allowed_hosts(cls):
        return cls._env().list('ALLOWED_HOSTS', default=[])

    @classmethod
    def csrf_trusted_origins(cls):
        return cls._env().list('CSRF_TRUSTED_ORIGINS', default=[])

    @classmethod
    def internal_ips(cls):
        return cls._env().list('INTERNAL_IPS', default=[])

    @classmethod
    def db_host(cls):
        return cls._env().str('DB_HOST', default='localhost')

    @classmethod
    def db_port(cls):
        return cls._env().int('DB_PORT', default=5432)

    @classmethod
    def db_name(cls):
        return cls._env().str('DB_NAME', default='dev_srs_cms')

    @classmethod
    def db_user(cls):
        return cls._env().str('DB_USER', default='postgres')

    @classmethod
    def db_pass(cls):
        return cls._env().str('DB_PASS', default=None)

    @classmethod
    def email_backend(cls):
        return cls._env().str('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')

    @classmethod
    def email_host(cls):
        return cls._env().str('EMAIL_HOST', default="")

    @classmethod
    def email_port(cls):
        return cls._env().str('EMAIL_PORT', default="")

    @classmethod
    def email_use_tls(cls):
        return cls._env().str('EMAIL_USE_TLS', default="")

    @classmethod
    def email_host_user(cls):
        return cls._env().str('EMAIL_HOST_USER', default="")

    @classmethod
    def email_host_password(cls):
        return cls._env().str('EMAIL_HOST_PASSWORD', default="")

    @classmethod
    def default_from_email(cls):
        return cls._env().str('DEFAULT_FROM_EMAIL', default="")

    @classmethod
    def odk_base_url(cls):
        return cls._env().str('ODK_BASE_URL', default=None)

    @classmethod
    def odk_username(cls):
        return cls._env().str('ODK_USERNAME', default=None)

    @classmethod
    def odk_password(cls):
        return cls._env().str('ODK_PASSWORD', default=None)

    @classmethod
    def odk_api_form_submission_page_size(cls):
        return cls._env().int('ODK_API_FORM_SUBMISSION_PAGE_SIZE', default=100)

    @classmethod
    def npm_bin_path(cls):
        return cls._env().str('NPM_BIN_PATH', default=None)
