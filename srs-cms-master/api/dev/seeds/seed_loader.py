import os
import glob
from pathlib import Path
from django.core.management import call_command
from api.models import User, OdkProject, OdkFormImporter, EtlDocument, OdkEntityList, Death, Staff, Province
from api.common.utils import Utils
from config.env import Env
from django.contrib.auth.models import Group


class SeedLoader:
    ENVS = [
        'dev',
        'test',
        'staging',
        'production'
    ]

    def __init__(self, env='dev'):
        if env not in self.ENVS:
            raise Exception('Environment not supported')
        self.env = env

    def seeds_root_dir(self):
        return str(Path(__file__).resolve().parent)

    def env_seeds_dir(self):
        return os.path.join(self.seeds_root_dir(), self.env)

    def seed_all(self, with_test_data=True):
        self.load_permissions()
        self.load_provinces()
        self.load_clusters()
        self.load_areas()
        self.load_staff()
        self.seed_users()
        self.seed_etl()
        self.seed_odk()
        if with_test_data:
            self.generate_test_data()

    def load_permissions(self):
        call_command('load_permissions')

    def load_provinces(self):
        csv_path = None
        if self.env == 'dev':
            csv_path = Env.get('DEV_LOAD_PROVINCES_CSV', default=None)

        if not csv_path:
            csv_path = os.path.join(self.env_seeds_dir(), 'provinces.csv')

        if csv_path:
            call_command('load_provinces', csv_path)

    def load_clusters(self):
        csv_path = None
        if self.env == 'dev':
            csv_path = Env.get('DEV_LOAD_CLUSTERS_CSV', default=None)

        if not csv_path:
            csv_path = os.path.join(self.env_seeds_dir(), 'clusters.csv')

        if csv_path:
            call_command('load_clusters', csv_path)

    def load_areas(self):
        csv_path = None
        if self.env == 'dev':
            csv_path = Env.get('DEV_LOAD_AREAS_CSV', default=None)

        if not csv_path:
            csv_path = os.path.join(self.env_seeds_dir(), 'areas.csv')

        if csv_path:
            call_command('load_areas', csv_path)

    def load_staff(self):
        csv_path = None
        if self.env == 'dev':
            csv_path = Env.get('DEV_LOAD_STAFF_CSV', default=None)

        if not csv_path:
            csv_path = os.path.join(self.env_seeds_dir(), 'staff.csv')

        if csv_path:
            call_command('load_staff', csv_path)

    def load_etl_mappings(self, filename, etl_document_id):
        abs_filename = os.path.join(self.env_seeds_dir(), filename)
        call_command('load_etl_documents', abs_filename, '--etl-document', etl_document_id)

    def seed_etl(self):
        filenames = glob.glob(os.path.join(self.env_seeds_dir(), 'etl_mappings*.json'))
        call_command('load_etl_documents', *filenames)

    def seed_odk(self):
        filename = os.path.join(self.env_seeds_dir(), 'odk_projects.json')
        call_command('load_odk_projects', filename)

    def generate_test_data(self):
        call_command('dev_generate_test_data')

    def seed_users(self):
        username = Env.get('DEV_SUPER_USER')
        email = Env.get('DEV_SUPER_USER_EMAIL')
        password = Env.get('DEV_SUPER_USER_PASS')

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            print('User created successfully: {}'.format(username))
        else:
            print('User already created: {}'.format(username))

        # Add Test Users
        test_users = [
            {
                'username': 'noaccess',
                'groups': []
            },
            {
                'username': 'province',
                'groups': [
                    'Province Users'
                ]
            },
            {
                'username': 'central',
                'groups': [
                    'Central Users'
                ]
            },
            {
                'username': 'administrator',
                'groups': [
                    'Administrator Users'
                ]
            }
        ]
        for user_config in test_users:
            username = user_config['username']

            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    password='password',
                    first_name=username,
                    last_name="User"
                )
                for group_name in user_config['groups']:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                    user.save()

                # Assign Provinces to the "province" user.
                if username == "province":
                    provinces = Province.objects.all()[:2]
                    if provinces:
                        user.provinces.add(*provinces)
                        user.save()
