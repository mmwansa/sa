from django.db import models, IntegrityError
from django.contrib.postgres.indexes import GinIndex
from api.models.decorators import db_timestamps
from api.models.query_extensions import QueryExtensionMixin
from api.common.type_caster import TypeCaster


@db_timestamps
class Event(QueryExtensionMixin, models.Model):
    class YesNo(models.IntegerChoices):
        YES = 1, 'Yes'
        NO = 2, 'No'

    class CmsStatusType(models.IntegerChoices):
        """
        Does not come from ODK. Used by the system/admins.
        """
        NORMAL = 1, 'Normal'
        DUPLICATE = 2, 'Duplicate'

    class EventType(models.IntegerChoices):  # okay
        NO_EVENT = 0, 'No Event'
        PREGNANCY = 1, 'Pregnancy'
        PREGNANCY_OUTCOME = 2, 'Pregnancy Outcome'
        DEATH = 3, 'Death'

    class VisitType(models.IntegerChoices):  # okay
        ROUTINE_VISIT = 1, 'Routine Visit'
        SPECIAL_VISIT = 2, 'Special Visit'

    class ConsentType(models.IntegerChoices):  # okay
        GENERAL = 1, 'General'
        SPECIAL_CASE = 2, 'Special Case'

    class EventRegisterType(models.IntegerChoices):
        YES = 1, 'Yes'
        NO = 2, 'No'
        HOUSEHOLD_MOVED = 3, 'Household Moved'
        HOUSEHOLD_ABSENT = 4, 'Household Absent'
        HOUSE_DESTROYED = 5, 'House Destroyed'

    class BirthOutcomeType(models.IntegerChoices):
        LIVE_BIRTH = 1, 'Live birth'
        STILLBIRTH = 2, 'Still birth'

    class AgeUnitType(models.IntegerChoices):
        DAYS = 1, 'Days'
        MONTHS = 2, 'Months'
        YEARS = 3, 'Years'

    class HealthCardSeen(models.IntegerChoices):
        YES_SEEN = 1, 'Yes, seen'
        YES_NOT_SEEN = 2, 'Yes, not seen'
        NO = 3, 'No'

    class SexType(models.IntegerChoices):
        MALE = 1, 'Male'
        FEMALE = 2, 'Female'

    class EventLocationType(models.IntegerChoices):
        HEALTH_FACILITY = 1, 'Health Facility'
        HOME = 2, 'Home'
        OTHER = 3, 'Other'

    class PhoneAllow(models.IntegerChoices):
        YES = 1, 'Yes'
        NO_CANNOT_GIVE = 2, 'No, I cannot give it to you'
        DONT_KNOW = 3, 'Don\'t know'

    class ResPhoneCellType(models.IntegerChoices):
        YES = 1, 'Yes'
        NO = 2, 'No'
        RESPONDENT_HEAD = 5, 'Respondent is the Head of Household'

    class VisitMethod(models.IntegerChoices):
        HOME_VISIT = 1, 'Home Visit'
        PHONE_CONTACT = 2, 'Phone Contact'

    cluster = models.ForeignKey(
        'Cluster',
        related_name='events',
        null=False,
        on_delete=models.RESTRICT,
        help_text='Foreign key to the Cluster.'
    )

    area = models.ForeignKey(
        'Area',
        related_name='events',
        null=False,
        on_delete=models.RESTRICT,
        help_text='Foreign key to the Area.'
    )

    event_staff = models.ForeignKey(
        'Staff',
        related_name='events',
        null=False,
        on_delete=models.RESTRICT,
        help_text='Foreign key to the Staff.'
    )

    # essential form information
    key = models.CharField(max_length=80, null=False, unique=True)
    cluster_code = models.CharField(max_length=255, blank=True, null=True)
    area_code = models.CharField(max_length=255, blank=True, null=True)
    staff_code = models.CharField(max_length=255, blank=True, null=True)
    submission_date = models.DateField(blank=True, null=True)
    interview_date = models.DateField(blank=True, null=True)
    # event_date = models.DateField(blank=True, null=True)  #TODO:REMOVE Check
    event_type = models.IntegerField(choices=EventType.choices, null=True)
    event_register = models.IntegerField(choices=EventRegisterType.choices, null=True)
    consent = models.IntegerField(choices=YesNo.choices, null=True)
    visit_type = models.IntegerField(choices=VisitType.choices, null=True)
    consent_type = models.IntegerField(choices=ConsentType.choices, null=True)

    household_code = models.CharField(max_length=255, blank=True, null=True)
    household_address = models.CharField(max_length=255, blank=True, null=True)
    household_head_name = models.CharField(max_length=255, blank=True, null=True)
    visit_method = models.IntegerField(choices=VisitMethod.choices, null=True)
    gps_latitude = models.DecimalField(max_digits=38, decimal_places=10, blank=True, null=True)
    gps_longitude = models.DecimalField(max_digits=38, decimal_places=10, blank=True, null=True)
    gps_altitude = models.DecimalField(max_digits=38, decimal_places=10, blank=True, null=True)
    gps_accuracy = models.DecimalField(max_digits=38, decimal_places=10, blank=True, null=True)
    respondent_name = models.CharField(max_length=255, blank=True, null=True)
    event_location = models.IntegerField(choices=EventLocationType.choices, null=True)

    # common all event types
    #event_person_name = models.CharField(max_length=255, blank=True, null=True)  #TODO:REMOVE check
    #person_age = models.IntegerField(null=True)  #TODO:REMOVE

    # common pregnancy and pregnancy outcome
    health_card = models.IntegerField(choices=HealthCardSeen.choices, null=True)
    mother_name = models.CharField(max_length=255, blank=True, null=True)
    mother_age_years = models.IntegerField(null=True)

    # pregnancy only
    lmp_date = models.DateField(blank=True, null=True)
    preg_ga_months = models.CharField(max_length=255, blank=True, null=True)
    edd_date = models.DateField(blank=True, null=True)

    # death only
    dec_person_name = models.CharField(max_length=255, blank=True, null=True)
    death_date = models.DateField(blank=True, null=True)
    dec_sex = models.IntegerField(choices=SexType.choices, null=True)
#    sex = models.IntegerField(choices=SexType.choices, null=True) #TODO: REMOVE
    dec_age_val = models.IntegerField(null=True)
    age_unit = models.CharField(choices=AgeUnitType.choices, null=True)
    dob_known = models.IntegerField(choices=YesNo.choices, null=True)
    dob_date = models.DateField(blank=True, null=True)
    dec_best_dob_date = models.DateField(blank=True, null=True)
    age_in_days = models.CharField(max_length=255, blank=True, null=True)
    age_in_years = models.CharField(max_length=255, blank=True, null=True)
    age_in_years_remain = models.CharField(max_length=255, blank=True, null=True)
    age_in_months = models.CharField(max_length=255, blank=True, null=True)
    age_in_months_remain = models.CharField(max_length=255, blank=True, null=True)
    is_neonatal = models.BooleanField(null=True)
    is_child = models.BooleanField(null=True)
    is_adult = models.BooleanField(null=True)
    deceased_mother_name = models.CharField(max_length=255, blank=True, null=True)
    deceased_father_name = models.CharField(max_length=255, blank=True, null=True)
    deceased_preg = models.IntegerField(choices=YesNo.choices, null=True)
    woman_died_birth = models.IntegerField(choices=YesNo.choices, null=True)
    woman_died_2mpp = models.IntegerField(choices=YesNo.choices, null=True)
    va_proposed_date = models.DateField(blank=True, null=True)
    va_contact_name = models.CharField(max_length=255, blank=True, null=True)
    va_contact_tel = models.CharField(max_length=255, blank=True, null=True)
    va_contact_tel_conf = models.CharField(max_length=255, blank=True, null=True)

    # pregnancy outcome only
    preg_outcome_date = models.DateField(blank=True, null=True)
    birth_sing_outcome = models.IntegerField(choices=BirthOutcomeType.choices, null=True,
                                             help_text="Was the baby born alive, born dead or lost before birth? (live birth=1; stillbirth=2; miscarriage/abortion=3).")
    birth_multi = models.IntegerField(choices=YesNo.choices, null=True, help_text="Was it multiple births?")
    birth_multi_alive = models.IntegerField(null=True, help_text="How many are born alive?")
    birth_multi_still = models.IntegerField(null=True, help_text="How many are born dead(stillbirths)?")
    baby_ct = models.CharField(max_length=255, blank=True, null=True, help_text="Number of babies to register.")
    baby_rep_count = models.CharField(max_length=255, blank=True, null=True, help_text="Registration of births.")

    # contact info
    head_phone_cell = models.IntegerField(choices=YesNo.choices, null=True)
    head_phone_allow = models.IntegerField(choices=PhoneAllow.choices, null=True)
    head_phone = models.CharField(max_length=255, blank=True, null=True)
    head_phone_confirm = models.CharField(max_length=255, blank=True, null=True)
    res_phone_cell = models.IntegerField(choices=ResPhoneCellType.choices, null=True)
    res_phone_allow = models.IntegerField(choices=PhoneAllow.choices, null=True)
    res_phone = models.CharField(max_length=255, blank=True, null=True)
    res_phone_confirm = models.CharField(max_length=255, blank=True, null=True)
    any_phone_cell = models.IntegerField(choices=YesNo.choices, null=True)
    any_phone_allow = models.IntegerField(choices=PhoneAllow.choices, null=True)
    any_phone_name = models.CharField(max_length=255, blank=True, null=True)
    any_phone = models.CharField(max_length=255, blank=True, null=True)
    any_phone_confirm = models.CharField(max_length=255, blank=True, null=True)

    # general form information
    start_datetime = models.DateTimeField(blank=True, null=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    today_date = models.DateField(blank=True, null=True)
    attachments_present = models.IntegerField(blank=True, null=True)
    attachments_expected = models.IntegerField(blank=True, null=True)
    device_code = models.CharField(max_length=255, blank=True, null=True)
    instance_code = models.CharField(max_length=255, blank=True, null=True)
    instance_name = models.CharField(max_length=255, blank=True, null=True)
    submitter_id = models.IntegerField(blank=True, null=True)
    submitter_name = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    review_state = models.CharField(max_length=255, blank=True, null=True)
    edits = models.IntegerField(blank=True, null=True)
    form_version = models.CharField(max_length=255, blank=True, null=True)
    cms_status = models.IntegerField(choices=CmsStatusType.choices, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'events'
        indexes = [
            # For text search.
            GinIndex(fields=['household_head_name'], name='events_gin_household_head_name',
                     opclasses=['gin_trgm_ops']),
            GinIndex(fields=['dec_person_name'], name='events_gin_dec_person_name',
                     opclasses=['gin_trgm_ops']),
            GinIndex(fields=['respondent_name'], name='events_gin_respondent_name',
                     opclasses=['gin_trgm_ops']),
        ]

    def __str__(self):
        return f"Event: {self.EventType(self.event_type).label} ({self.id})"

    def formatted_gps_coordinates(self):
        """
        Gets the GPS coordinates as a string formatted as: "Latitude Longitude Altitude Accuracy"
        """
        if not (self.gps_latitude and self.gps_longitude):
            return ''

        parts = [self.gps_latitude, self.gps_longitude]
        if self.gps_altitude:
            parts.append(self.gps_altitude)
        if self.gps_accuracy:
            parts.append(self.gps_accuracy)
        return ' '.join(map(str, parts))


@db_timestamps
class Baby(QueryExtensionMixin, models.Model):
    class SexType(models.IntegerChoices):
        MALE = 1, 'Male'
        FEMALE = 2, 'Female'

    event = models.ForeignKey(
        Event,
        related_name='babies',
        null=False,
        on_delete=models.CASCADE,
        help_text='Foreign key to parent Event.'
    )
    key = models.CharField(max_length=80, null=False, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    sex = models.IntegerField(choices=SexType.choices, null=True)
    preg_outcome_date = models.DateField(blank=True, null=True)
    weight = models.FloatField(null=True)
    is_birth_registered = models.BooleanField(null=True)

    class Meta:
        managed = True
        db_table = 'babies'

    def __str__(self):
        return f" {self.name} ({self.id})"


@db_timestamps
class Death(QueryExtensionMixin, models.Model):
    class DeathType(models.IntegerChoices):
        NORMAL = 2, 'Normal Death'
        STILLBIRTH = 3, 'Stillbirth'

    class DeathStatus(models.IntegerChoices):
        NEW_DEATH = 0, 'New Death'
        VA_SCHEDULED = 1, 'VA Scheduled'
        VA_COMPLETED = 2, 'VA Completed'
        VA_ON_HOLD = 3, 'VA On Hold'

    class SexType(models.IntegerChoices):
        MALE = 1, 'Male'
        FEMALE = 2, 'Female'

    event = models.ForeignKey(
        Event,
        related_name='deaths',
        null=False,
        on_delete=models.CASCADE,
        help_text='Foreign key to parent Event.'
    )

    va_staff = models.ForeignKey(
        'Staff',
        related_name='deaths',
        null=True,
        on_delete=models.RESTRICT,
        help_text='Foreign key to the Staff.'
    )

    key = models.CharField(max_length=80, null=False, unique=True)
    death_type = models.IntegerField(choices=DeathType.choices, null=True)
    death_code = models.CharField(max_length=20, null=True, unique=True, verbose_name='Death Code')
    death_status = models.IntegerField(choices=DeathStatus.choices, null=True)
    deceased_name = models.CharField(max_length=255, blank=True, null=True)
    deceased_sex = models.IntegerField(choices=SexType.choices, null=True)
    deceased_dob = models.DateField(blank=True, null=True, help_text='Date of birth')
    deceased_dod = models.DateField(blank=True, null=True, help_text='Date of death')
    deceased_age = models.IntegerField(null=True)
    deceased_mother_name = models.CharField(max_length=255, blank=True, null=True)
    deceased_father_name = models.CharField(max_length=255, blank=True, null=True)
    va_key = models.CharField(max_length=80, blank=True, null=True)
    va_proposed_date = models.DateField(blank=True, null=True)
    va_scheduled_date = models.DateField(blank=True, null=True)
    va_completed_date = models.DateField(blank=True, null=True)
    va_max_date = models.DateTimeField(blank=True, null=True)
    va_staff_code = models.CharField(max_length=12, blank=True, null=True)
    comment = models.CharField(max_length=2000, blank=True, null=True)
    match_err = models.IntegerField(blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'deaths'
        constraints = [
            models.UniqueConstraint(fields=['death_code'], name='unique_death_code'),
        ]
        indexes = [
            # For text search.
            GinIndex(fields=['death_code'], name='deaths_gin_death_code', opclasses=['gin_trgm_ops']),
            GinIndex(fields=['deceased_name'], name='events_gin_deceased_name', opclasses=['gin_trgm_ops']),
        ]

    def __str__(self):
        return f"{self.death_code} - {self.DeathType(self.death_type).label}  ({self.id})"

    def save_with_death_code(self, force_new_id=False):
        """
        Generate a unique death_code and saves self.
        This will attempt to insert the record and use the death_code unique constraint to retry until successful.

        death_code format:
            self.event.cluster.code + sequential number(left padded to 4 characters with '0')

        Args:
            force_new_id: True to generate a new death_code otherwise raise exception if death_code already exists.
                This will prevent the death_code from being overwritten.

        Returns:
            True if successful, False otherwise.
        """
        if force_new_id and self.death_code:
            self.death_code = None
        elif not force_new_id and self.death_code:
            raise Exception('death_code already set: {}'.format(str(self.death_code)))

        cluster_code = self.event.cluster.code
        max_attempts = 10
        attempt_number = 0
        while attempt_number <= max_attempts:
            attempt_number += 1
            last_cluster_death = Death.objects.filter(
                death_code__istartswith=cluster_code
            ).order_by('-death_code').first()

            next_id = 1
            if last_cluster_death:
                next_id = TypeCaster.to_int(last_cluster_death.death_code[-4:]) + 1

            self.death_code = '{}{}'.format(cluster_code, str(next_id).rjust(4, '0'))
            try:
                self.save()
                return True
            except IntegrityError:
                continue
        return False

    def set_va_completed(self, verbal_autopsy=None, save=True):
        """
        Updates VA fields from the linked VerbalAutopsy.

        Args:
            save: Save the death record after updating.

        Returns:
            None
        """
        verbal_autopsy = verbal_autopsy if verbal_autopsy else self.verbal_autopsy

        if not verbal_autopsy:
            raise Exception("VerbalAutopsy not set.")
        self.verbal_autopsy = verbal_autopsy
        self.death_status = Death.DeathStatus.VA_COMPLETED
        self.va_key = self.verbal_autopsy.key
        self.va_completed_date = self.verbal_autopsy.today_date
        if save:
            self.save()


@db_timestamps
class Pregnancy(QueryExtensionMixin, models.Model):
    event = models.ForeignKey(
        Event,
        related_name='pregnancies',
        null=False,
        on_delete=models.CASCADE,
        help_text='Foreign key to parent Event.'
    )
    staff = models.ForeignKey(
        'Staff',
        related_name='pregnancies',
        null=False,
        on_delete=models.RESTRICT,
        help_text='Foreign key to the Staff.'
    )
    code = models.CharField(max_length=20, null=True, unique=True)
    outcome_key = models.CharField(max_length=80, blank=True, null=True)
    edd_date = models.DateTimeField(blank=True, null=True)
    preg_staff_code = models.CharField(max_length=12, blank=True, null=True)
    outcome_staff_code = models.CharField(max_length=12, blank=True, null=True)
    outcome_status = models.IntegerField(blank=True, null=True)
    comment = models.CharField(max_length=2000, blank=True, null=True)
    match_err = models.IntegerField(blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'pregnancies'
        indexes = [
            # For text search.
            GinIndex(fields=['code'], name='pregnancies_gin_code', opclasses=['gin_trgm_ops'])
        ]

    def __str__(self):
        return f"{self.code} ({self.id})"
