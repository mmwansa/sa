import os
import csv
from django.core.management.base import BaseCommand
from api.models import Staff, Cluster, Province
from api.common import Utils


class Command(BaseCommand):
    help = "Load Staff from CSV."

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
            self.stdout.write("Loading staff...")
            with open(csv_file, newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                expected_headers = [
                    "code",
                    "cluster_code",
                    "province_code",
                    "staff_type_id",
                    "full_name",
                    "title",
                    "mobile_per",
                    "email",
                    "cms_status",
                    "comment"
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
                    staff_code = row["code"]
                    staff_type = Staff.StaffType(row.get("staff_type_id"))
                    cluster_code = row.get("cluster_code")
                    province_code = row.get("province_code")

                    staff = Staff.find_by(code=staff_code)
                    cluster = Cluster.find_by(code=cluster_code)
                    province = Province.find_by(code=province_code)

                    can_save = False
                    if staff_type == Staff.StaffType.VA and not province:
                        self.stderr.write(self.style.ERROR(f"Province not found: {province_code}"))
                    elif staff_type == Staff.StaffType.CSA and not cluster:
                        self.stderr.write(self.style.ERROR(f"Cluster not found: {cluster_code}"))
                    elif staff and staff.cluster == cluster and staff.province == province:
                        if verbose:
                            self.stdout.write(self.style.SUCCESS(f"Staff exists: {staff.code}"))
                    else:
                        if not staff:
                            staff = Staff(
                                cluster=cluster,
                                province=province,
                                code=staff_code,
                                staff_type=staff_type,
                                full_name=row.get("full_name"),
                                title=row.get("title"),
                                mobile_per=row.get("mobile_per"),
                                email=row.get("email"),
                                cms_status=row.get("cms_status"),
                                comment=row.get("comment")
                            )
                            can_save = True
                            if verbose:
                                self.stdout.write(self.style.SUCCESS(f"Loading Cluster: {cluster.code}"))
                        elif staff.cluster != cluster or staff.province != province:
                            if staff.cluster != cluster:
                                staff.cluster = cluster
                                can_save = True
                                if verbose:
                                    self.stdout.write(self.style.SUCCESS(f"Updating Staff Cluster: {cluster.code}"))

                            if staff.province != province:
                                staff.province = province
                                can_save = True
                                if verbose:
                                    self.stdout.write(self.style.SUCCESS(f"Updating Staff Province: {province.code}"))

                    if can_save:
                        staff.save()
                        total_loaded += 1

                self.stdout.write(self.style.SUCCESS(f"Loaded {total_loaded} staff."))
        except Exception as ex:
            self.stderr.write(self.style.ERROR(f"An error occurred: {ex}"))
