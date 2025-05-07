from django.db import models
from api.models.decorators import db_timestamps
from api.models.query_extensions import QueryExtensionMixin


@db_timestamps
class VerbalAutopsy(QueryExtensionMixin, models.Model):
    class CmsStatusType(models.TextChoices):
        """
        Does not come from ODK. Used by the system/admins.
        """
        NORMAL = '1', 'Normal'
        DUPLICATE = '2', 'Duplicate'

    cluster = models.ForeignKey(
        'Cluster',
        related_name='verbal_autopsies',
        null=False,
        on_delete=models.RESTRICT,
        help_text='Foreign key to the Cluster.'
    )

    area = models.ForeignKey(
        'Area',
        related_name='verbal_autopsies',
        null=False,
        on_delete=models.RESTRICT,
        help_text='Foreign key to the Area.'
    )

    death = models.OneToOneField(
        'Death',
        on_delete=models.RESTRICT,
        null=True,
        related_name="verbal_autopsy",
        help_text='Foreign key to the Death.'
    )

    key = models.CharField(max_length=80, null=False, unique=True)
    submission_date = models.DateField(blank=True, null=True)
    deceased_list = models.CharField(max_length=80, null=False, unique=True)
    death_code = models.CharField(max_length=255, blank=True, null=True)
    cluster_code = models.CharField(max_length=255, blank=True, null=True)
    area_code = models.CharField(max_length=255, blank=True, null=True)
    household_id = models.CharField(max_length=255, blank=True, null=True)
    id10002 = models.CharField(max_length=255, blank=True, null=True)
    id10003 = models.CharField(max_length=255, blank=True, null=True)
    id10004 = models.CharField(max_length=255, blank=True, null=True)
    id10007 = models.CharField(max_length=255, blank=True, null=True)
    id10008 = models.CharField(max_length=255, blank=True, null=True)
    id10009 = models.CharField(max_length=255, blank=True, null=True)
    id10010 = models.CharField(max_length=255, blank=True, null=True)
    id10012 = models.CharField(max_length=255, blank=True, null=True)
    id10013 = models.CharField(max_length=255, blank=True, null=True)
    id10011 = models.DateField(blank=True, null=True)
    id10017 = models.CharField(max_length=255, blank=True, null=True)
    id10018 = models.CharField(max_length=255, blank=True, null=True)
    id10019 = models.CharField(max_length=255, blank=True, null=True)
    id10020 = models.CharField(max_length=255, blank=True, null=True)
    id10021 = models.DateField(blank=True, null=True)
    id10022 = models.CharField(max_length=255, blank=True, null=True)
    id10023_a = models.DateField(blank=True, null=True)
    id10023_b = models.CharField(max_length=255, blank=True, null=True)
    id10023 = models.DateField(blank=True, null=True)
    id10024 = models.CharField(max_length=255, blank=True, null=True)
    ageindays = models.IntegerField(blank=True, null=True)
    ageinyears = models.IntegerField(blank=True, null=True)
    ageinyearsremain = models.IntegerField(blank=True, null=True)
    ageinmonths = models.IntegerField(blank=True, null=True)
    ageinmonthsremain = models.IntegerField(blank=True, null=True)
    isneonatal1 = models.IntegerField(blank=True, null=True)
    ischild1 = models.IntegerField(blank=True, null=True)
    isadult1 = models.IntegerField(blank=True, null=True)
    displayageneonate = models.IntegerField(blank=True, null=True)
    displayagechild = models.IntegerField(blank=True, null=True)
    displayageadult = models.IntegerField(blank=True, null=True)
    age_group = models.IntegerField(blank=True, null=True)
    age_neonate_days = models.IntegerField(blank=True, null=True)
    age_child_unit = models.IntegerField(blank=True, null=True)
    age_child_days = models.IntegerField(blank=True, null=True)
    age_child_months = models.IntegerField(blank=True, null=True)
    age_child_years = models.IntegerField(blank=True, null=True)
    age_adult = models.IntegerField(blank=True, null=True)
    ageinmonthsbyyear = models.IntegerField(blank=True, null=True)
    ageinyears2 = models.IntegerField(blank=True, null=True)
    isneonatal2 = models.IntegerField(blank=True, null=True)
    ischild2 = models.IntegerField(blank=True, null=True)
    isadult2 = models.IntegerField(blank=True, null=True)
    isneonatal = models.IntegerField(blank=True, null=True)
    ischild = models.IntegerField(blank=True, null=True)
    isadult = models.IntegerField(blank=True, null=True)
    ageindaysneonate = models.IntegerField(blank=True, null=True)
    id10058 = models.CharField(max_length=255, blank=True, null=True)
    id10051 = models.CharField(max_length=255, blank=True, null=True)
    id10052 = models.CharField(max_length=255, blank=True, null=True)
    id10053 = models.CharField(max_length=255, blank=True, null=True)
    id10054 = models.CharField(max_length=255, blank=True, null=True)
    id10055 = models.CharField(max_length=255, blank=True, null=True)
    id10057 = models.CharField(max_length=255, blank=True, null=True)
    id10059 = models.CharField(max_length=255, blank=True, null=True)
    id10060_check = models.CharField(max_length=255, blank=True, null=True)
    id10060 = models.DateField(blank=True, null=True)
    id10061 = models.CharField(max_length=255, blank=True, null=True)
    id10062 = models.CharField(max_length=255, blank=True, null=True)
    id10063 = models.CharField(max_length=255, blank=True, null=True)
    id10064 = models.CharField(max_length=255, blank=True, null=True)
    id10065 = models.CharField(max_length=255, blank=True, null=True)
    id10066 = models.CharField(max_length=255, blank=True, null=True)
    id10069 = models.CharField(max_length=255, blank=True, null=True)
    id10069_a = models.CharField(max_length=255, blank=True, null=True)
    id10070 = models.CharField(max_length=255, blank=True, null=True)
    id10071_check = models.CharField(max_length=255, blank=True, null=True)
    id10071 = models.DateField(blank=True, null=True)
    id10072 = models.CharField(max_length=255, blank=True, null=True)
    id10073 = models.CharField(max_length=255, blank=True, null=True)
    id10481 = models.DateField(blank=True, null=True)

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
        db_table = 'verbal_autopsies'

    def __str__(self):
        return f"{self.death_code} - {self.today_date}"
