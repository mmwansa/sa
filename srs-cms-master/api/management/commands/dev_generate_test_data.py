from django.core.management.base import BaseCommand
from api.models import Event, Death, Province, Cluster, Area, Staff, Household, HouseholdMember
from datetime import datetime, date, timedelta
import uuid
from faker import Faker
import random


class Command(BaseCommand):
    help = "Generate Test Data"
    fake = Faker()

    def handle(self, *args, **kwargs):
        self.stdout.write('Generating Test Data...')
        self.generate_deaths()

    def generate_deaths(self):
        self.stdout.write('Generating Death Events...')
        total_death_events = 0
        for staff in Staff.objects.all():
            if staff.cluster:
                for area in staff.cluster.areas.all():
                    self._generate_death_event(staff.cluster, area, staff)
                    total_death_events += 1

            if staff.province:
                for cluster in staff.province.clusters.all():
                    for area in cluster.areas.all():
                        self._generate_death_event(cluster, area, staff)
                        total_death_events += 1

        self.stdout.write(self.style.SUCCESS(f'Generated Total Death Events: {total_death_events}'))

    def _generate_death_event(self, cluster, area, staff):
        event_key = uuid.uuid4()

        dob = self.fake.date_of_birth(minimum_age=0, maximum_age=65)
        dod = self.fake.date_this_month(before_today=True, after_today=True)
        #person_age = dod.year - dob.year - ((dod.month, dod.day) < (dob.month, dob.day))
        dec_age_val = (dod - dob).days
        lat_lang = self.fake.local_latlng()

        event = Event.objects.create(
            key=event_key,
            cluster_code=cluster.code,
            cluster=cluster,
            area=area,
            area_code=area.code,
            event_staff=staff,
            staff_code=staff.code,
            submission_date=datetime.today(),
            event_type=Event.EventType.DEATH,
            visit_type=Event.VisitType.ROUTINE_VISIT,
            consent_type=Event.ConsentType.GENERAL,
            visit_method=Event.VisitMethod.HOME_VISIT,
            # event_person_name=self.fake.name(),
            respondent_name=self.fake.name(),
            household_head_name=self.fake.name(),
            household_address=self.fake.street_address(),
            sex=self.fake.random_element(Death.SexType),
            dob_date=dob,
            death_date=dod,
            # person_age=person_age,
            dec_age_val=dec_age_val,
            deceased_mother_name=self.fake.name(),
            deceased_father_name=self.fake.name(),
            gps_latitude=lat_lang[0],
            gps_longitude=lat_lang[1],
            gps_altitude=round(random.uniform(0, 5000), 2),
            gps_accuracy=round(random.uniform(1, 50), 2),
            va_proposed_date=self.fake.date_this_month(before_today=False, after_today=True),
        )
        self._generate_death(event)
        return event

    def _generate_death(self, event):
        death = Death(
            key=event.key,
            event=event,
            death_status=self.fake.random_element(Death.DeathStatus),
            death_type=self.fake.random_element(Death.DeathType),
            va_proposed_date=event.va_proposed_date,
            deceased_name=event.dec_person_name,
            deceased_sex=event.sex,
            deceased_dob=event.dob_date,
            deceased_dod=event.death_date,
            deceased_age=event.dec_age_val,
            # deceased_age=event.person_age,
            deceased_mother_name=event.deceased_mother_name,
            deceased_father_name=event.deceased_father_name,
        )

        if death.death_status == Death.DeathStatus.VA_SCHEDULED or death.death_status == Death.DeathStatus.VA_COMPLETED:
            date_start = event.death_date + timedelta(days=1)
            date_start = self.fake.date_between_dates(date_start=date_start, date_end=date_start + timedelta(days=15))
            date_end = date_start + timedelta(days=30)
            death.va_scheduled_date = self.fake.date_between_dates(date_start=date_start, date_end=date_end)
            death.va_staff = event.event_staff

        if death.death_status == Death.DeathStatus.VA_COMPLETED:
            date_start = death.va_scheduled_date + timedelta(days=1)
            date_end = date_start + timedelta(days=30)
            death.va_completed_date = self.fake.date_between_dates(date_start=date_start, date_end=date_end)

        if not death.save_with_death_code():
            self.stderr.write(self.style.ERROR("Failed to save with death code"))
            return death
        else:
            return None
