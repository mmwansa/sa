from argparse import ArgumentError
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission
from django.http import HttpRequest
from django.contrib.auth import get_user_model


class Permissions:
    class Codes:
        SCHEDULE_VA = 'auth.schedule_va'
        VIEW_ASSIGNED_PROVINCES = 'auth.view_assigned_provinces'
        VIEW_ALL_PROVINCES = 'auth.view_all_provinces'

    @classmethod
    def has_permission(cls, user_or_request, permission_code):
        if isinstance(user_or_request, HttpRequest):
            user = user_or_request.user
        elif isinstance(user_or_request, get_user_model()):
            user = user_or_request
        else:
            raise ArgumentError('user_or_request must be either a HttpRequest or {}'.format(get_user_model()))
        return user.has_perm(permission_code)

    @classmethod
    def _create(cls, verbose=False):
        cls._create_permissions(verbose=verbose)
        cls._create_groups(verbose=verbose)

    @classmethod
    def _create_permissions(cls, verbose=False):
        print('Importing Permissions...')
        content_type = ContentType.objects.get_for_model(Permission)

        global_permissions = [
            (cls.Codes.SCHEDULE_VA.replace('auth.', ''), 'Can schedule VA'),
            (cls.Codes.VIEW_ASSIGNED_PROVINCES.replace('auth.', ''), 'Can view assigned provinces'),
            (cls.Codes.VIEW_ALL_PROVINCES.replace('auth.', ''), 'Can view all provinces'),
        ]

        for codename, name in global_permissions:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=content_type,
            )
            if verbose:
                if created:
                    print(f"Created Permission '{name}'")
                else:
                    print(f"Already exists, Permission '{name}'")

    @classmethod
    def _create_groups(cls, verbose=False):
        print('Importing Groups...')
        group_permissions = {
            'Province Users': [
                cls.Codes.SCHEDULE_VA.replace('auth.', ''),
                cls.Codes.VIEW_ASSIGNED_PROVINCES.replace('auth.', '')
            ],
            'Central Users': [
                cls.Codes.SCHEDULE_VA.replace('auth.', ''),
                cls.Codes.VIEW_ALL_PROVINCES.replace('auth.', '')
            ],
            'Administrator Users': [
                cls.Codes.SCHEDULE_VA.replace('auth.', ''),
                cls.Codes.VIEW_ALL_PROVINCES.replace('auth.', '')
            ],
        }

        for group_name, permissions in group_permissions.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if verbose:
                if created:
                    print(f"Create Group '{group_name}'")
                else:
                    print(f"Already exists, Group: '{group_name}'")

            for codename in permissions:
                permission = Permission.objects.get(codename=codename)
                if not permission in group.permissions.all():
                    group.permissions.add(permission)
                    verbose and print(f"Assigned '{permission.name}' to '{group_name}'.")
