#!/usr/bin/env python3

import os
import sys
import json
import django
from django.db.models import (
    CharField, TextField, BooleanField, IntegerField, FloatField, DateField, DateTimeField, DecimalField, JSONField
)
from django.contrib.postgres.fields import ArrayField

script_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(script_dir, '..'))

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

# Import Models to generate mappings for.
from api.models import Event, Baby, Death, Household, HouseholdMember, Staff, Province
from api.common import TypeCaster

ALL_MODELS = [
    Event,
    Baby,
    Death,
    Household,
    HouseholdMember,
    Staff,
    Province
]


def to_target_type(field):
    if isinstance(field, (CharField, TextField)):
        return TypeCaster.TypeCode.STR
    elif isinstance(field, BooleanField):
        return TypeCaster.TypeCode.BOOL
    elif isinstance(field, (IntegerField, FloatField, DecimalField)):
        return TypeCaster.TypeCode.FLOAT if isinstance(field, DecimalField) else TypeCaster.TypeCode.INT
    elif isinstance(field, DateField):
        return TypeCaster.TypeCode.DATE
    elif isinstance(field, DateTimeField):
        return TypeCaster.TypeCode.DATETIME
    elif isinstance(field, JSONField):
        return TypeCaster.TypeCode.DICT
    elif isinstance(field, ArrayField):
        return TypeCaster.TypeCode.LIST
    else:
        return TypeCaster.TypeCode.STR


def main():
    for model in ALL_MODELS:
        print('=' * 80)
        print('Model: {}'.format(model.__name__))

        fields = model._meta.get_fields()
        model_mappings_json = []
        for field in fields:
            # Skip the 'id' field.
            if field.name == 'id':
                continue
            # Ignore reverse and many-to-many relationships
            if not (hasattr(field, 'column') and field.column):
                continue

            model_mappings_json.append(
                {
                    "source_name": '',
                    "target_name": field.name,
                    "target_type": to_target_type(field),
                    "default": None,
                    "transform": None,
                    "is_primary_key": field.primary_key,
                    "is_enabled": False,
                    "is_required": True
                }
            )

        print(json.dumps(model_mappings_json, indent=2, sort_keys=False))


if __name__ == "__main__":
    main()
