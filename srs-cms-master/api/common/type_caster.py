from django.db import models
from django.utils.timezone import is_naive, make_aware
from datetime import datetime, date
import dateutil.parser


class TypeCaster:
    class TypeCode(models.TextChoices):
        INT = 'int', 'Int'
        FLOAT = 'float', 'Float'
        STR = 'str', 'String'
        BOOL = 'bool', 'Boolean'
        DICT = 'dict', 'Dictionary'
        LIST = 'list', 'List'
        DATE = 'date', 'Date'
        DATETIME = 'datetime', 'Datetime'

    @classmethod
    def get(cls, code):
        if code not in cls.TypeCode.values:
            raise ValueError('Invalid type code: {}. Must be one of: {}'.format(code, ','.join(cls.TypeCode.values)))
        attr_name = 'to_{}'.format(code)
        return getattr(cls, attr_name)

    @classmethod
    def cast(cls, value, type_code, default=None):
        method = cls.get(type_code)
        result = method(value, default=default)
        return result

    @classmethod
    def to_int(cls, value, default=None):
        """Cast value to int."""
        try:
            return default if value is None else int(value)
        except (ValueError, TypeError):
            raise

    @classmethod
    def to_float(cls, value, default=None):
        """Cast value to float."""
        try:
            return default if value is None else float(value)
        except (ValueError, TypeError):
            raise

    @classmethod
    def to_bool(cls, value, default=None):
        """Cast value to bool."""
        try:
            if isinstance(value, str):
                value = value.strip().lower()
                if value in {'true', 'yes', '1'}:
                    return True
                if value in {'false', 'no', '0'}:
                    return False
            return bool(value)
        except (ValueError, TypeError):
            raise

    @classmethod
    def to_str(cls, value, default=None):
        """Cast value to str."""
        try:
            if value is None:
                return default
            else:
                return str(value)
        except (ValueError, TypeError):
            raise

    @classmethod
    def to_list(cls, value, default=None, delimiter=','):
        """Cast value to list."""
        try:
            if value is None:
                return default
            elif isinstance(value, str):
                return value.split(delimiter)
            else:
                return list(value)
        except (ValueError, TypeError):
            raise

    @classmethod
    def to_dict(cls, value, default=None):
        """Cast value to dict."""
        try:
            if value is None:
                return default
            elif isinstance(value, str):
                import json
                return json.loads(value)
            elif isinstance(value, dict):
                return value
            else:
                return default
        except (ValueError, TypeError, json.JSONDecodeError):
            raise

    @classmethod
    def to_date(cls, value, default=None):
        """Cast value to a date (datetime.date)."""
        try:
            if isinstance(value, str):
                dt = dateutil.parser.isoparse(value).date()
            elif isinstance(value, datetime):
                dt = value.date()
            elif isinstance(value, date):
                dt = value
            else:
                return default

            return dt
        except (ValueError, TypeError, OverflowError) as ex:
            raise

    @classmethod
    def to_datetime(cls, value, default=None):
        """Cast value to a datetime (datetime.datetime), ensuring it is timezone-aware."""
        try:
            if isinstance(value, str):
                dt = dateutil.parser.isoparse(value)
            elif isinstance(value, datetime):
                dt = value
            else:
                return default

            if is_naive(dt):
                dt = make_aware(dt)
            return dt
        except (ValueError, TypeError, OverflowError) as ex:
            raise
