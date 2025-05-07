import os
import csv
from django.core.management.base import BaseCommand
from api.models import Cluster, Province
from api.common import Utils


class Command(BaseCommand):
    help = "Load Clusters from CSV."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="The path to the CSV file to be loaded.",
        )
        parser.add_argument(
            '--verbose',
            default=False,
            action='store_true',
            help='Print extra details.'
        )

    def handle(self, *args, **kwargs):
        csv_file = Utils.expand_path(kwargs["csv_file"])
        verbose = kwargs['verbose']

        if not os.path.exists(csv_file):
            self.stderr.write(self.style.ERROR(f"File not found: {csv_file}"))
            return

        try:
            self.stdout.write("Loading Clusters...")
            with open(csv_file, newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                expected_headers = [
                    "code",
                    "name",
                    "province_code"
                ]
                missing_headers = []
                for header in expected_headers:
                    if header not in reader.fieldnames:
                        missing_headers.append(header)
                if missing_headers:
                    self.stderr.write(self.style.ERROR(f"Missing CSV headers: {', '.join(missing_headers)}"))
                    return

                total_loaded = 0
                for row in reader:
                    cluster_code = row.get("code")
                    province_code = row.get("province_code")

                    cluster = Cluster.find_by(code=cluster_code)
                    province = Province.find_by(code=province_code)

                    can_save = False
                    if not province:
                        self.stderr.write(self.style.ERROR(f"Province not found: {province_code}"))
                    elif cluster and province and cluster.province == province:
                        if verbose:
                            self.stdout.write(self.style.SUCCESS(f"Cluster exists: {cluster.code}"))
                    else:
                        if not cluster:
                            cluster = Cluster(
                                province=province,
                                code=cluster_code,
                                name=row.get("name")
                            )
                            can_save = True
                            if verbose:
                                self.stdout.write(self.style.SUCCESS(f"Loading Cluster: {cluster.code}"))
                        elif cluster.province != province:
                            cluster.province = province
                            can_save = True
                            if verbose:
                                self.stdout.write(self.style.SUCCESS(f"Updating Cluster Province: {province.code}"))

                    if can_save:
                        cluster.save()
                        total_loaded += 1

                self.stdout.write(self.style.SUCCESS(f"Loaded {total_loaded} clusters."))
        except Exception as ex:
            self.stderr.write(self.style.ERROR(f"An error occurred: {ex}"))
