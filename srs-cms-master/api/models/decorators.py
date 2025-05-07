from django.db import models


def db_timestamps(cls):
    """
    Decorator that adds a timestamp fields to a model class.
    Example:
        @db_timestamps
        class Foo(models.Model):
            pass
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cls.add_to_class('created_at', created_at)
    cls.add_to_class('updated_at', updated_at)
    return cls
