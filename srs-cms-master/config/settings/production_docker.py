from .settings_base import *

STATIC_ROOT = '/app/static'
STATIC_URL = '/static/'
MEDIA_ROOT = '/app/media'
MEDIA_URL = '/media/'

SECURE_SSL_REDIRECT = Env.get("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = Env.get("SESSION_COOKIE_SECURE", default=True, cast=bool)
CSRF_COOKIE_SECURE = Env.get("CSRF_COOKIE_SECURE", default=True, cast=bool)
SECURE_BROWSER_XSS_FILTER = Env.get("SECURE_BROWSER_XSS_FILTER", default=True, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = Env.get("SECURE_CONTENT_TYPE_NOSNIFF", default=True, cast=bool)
