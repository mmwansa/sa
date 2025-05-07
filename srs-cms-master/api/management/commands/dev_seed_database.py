from django.core.management.base import BaseCommand
from api.dev.seeds.seed_loader import SeedLoader


class Command(BaseCommand):
    help = 'Seed the Database.'

    def add_arguments(self, parser):
        parser.add_argument('-e', '--env',
                            default='dev',
                            choices=SeedLoader.ENVS,
                            help='Run migrations')

        parser.add_argument('--with-test-data',
                            default=False,
                            action='store_true',
                            help='Load test data.')

    def handle(self, *args, **kwargs):
        env = kwargs['env']
        with_test_data = kwargs['with_test_data']
        SeedLoader(env=env).seed_all(with_test_data=with_test_data)
