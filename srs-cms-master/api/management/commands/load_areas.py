import os
import csv
from django.core.management.base import BaseCommand
from api.models import Area, Cluster
from api.common import Utils


class Command(BaseCommand):
    help = "Load Areas from CSV."

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
            self.stdout.write("Loading Areas...")
            with open(csv_file, newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                expected_headers = [
                    "code", "cluster_code", "prov_text_code", "adm0_code", "adm0_name",
                    "adm1_code", "adm1_name", "adm2_code", "adm2_name",
                    "adm3_code", "adm3_name", "adm4_code", "adm4_name",
                    "adm5_code", "adm5_name", "urban_rural",
                    "carto_house_count", "carto_pop_count", "import_code",
                    "status", "comment"
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
                    area_code = row.get("code")
                    cluster_code = row.get("cluster_code")

                    area = Area.find_by(code=area_code)
                    cluster = Cluster.find_by(code=cluster_code)

                    can_save = False
                    if not cluster:
                        self.stderr.write(self.style.ERROR(f"Cluster not found: {cluster_code}"))
                    elif area and cluster and area.cluster == cluster:
                        if verbose:
                            self.stdout.write(self.style.SUCCESS(f"Area exists: {area.code}"))
                    else:
                        if not area:
                            area = Area(
                                cluster=cluster,
                                code=area_code,
                                adm0_code=row.get("adm0_code"),
                                adm0_name=row.get("adm0_name"),
                                adm1_code=row.get("adm1_code"),
                                adm1_name=row.get("adm1_name"),
                                adm2_code=row.get("adm2_code"),
                                adm2_name=row.get("adm2_name"),
                                adm3_code=row.get("adm3_code"),
                                adm3_name=row.get("adm3_name"),
                                adm4_code=row.get("adm4_code"),
                                adm4_name=row.get("adm4_name"),
                                adm5_code=row.get("adm5_code"),
                                adm5_name=row.get("adm5_name"),
                                urban_rural=row.get("urban_rural"),
                                carto_house_count=row.get("carto_house_count") or None,
                                carto_pop_count=row.get("carto_pop_count") or None,
                                import_code=row.get("import_code"),
                                status=row.get("status") or None,
                                comment=row.get("comment"),
                                province_code=row.get("prov_text_code")
                            )
                            can_save = True
                            if verbose:
                                self.stdout.write(self.style.SUCCESS(f"Loading Area: {area.code}"))
                        elif area.cluster != cluster:
                            area.cluster = cluster
                            can_save = True
                            if verbose:
                                self.stdout.write(self.style.SUCCESS(f"Updating Area Cluster: {cluster.code}"))

                    if can_save:
                        area.save()
                        total_loaded += 1

                self.stdout.write(self.style.SUCCESS(f"Loaded {total_loaded} areas."))
        except Exception as ex:
            self.stderr.write(self.style.ERROR(f"An error occurred: {ex}"))
