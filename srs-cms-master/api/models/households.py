from django.db import models
from api.models.decorators import db_timestamps
from api.models.query_extensions import QueryExtensionMixin


@db_timestamps
class Household(QueryExtensionMixin, models.Model):
    class YesNoType(models.IntegerChoices):
        YES = 1, 'Yes'
        NO = 2, 'No'

    class CmsStatusType(models.TextChoices):
        """
        Does not come from ODK. Used by the system/admins.
        """
        NORMAL = '1', 'Normal'
        DUPLICATE = '2', 'Duplicate'

    class MetStatusType(models.IntegerChoices):
        YES = 1, 'Adult member of household met'
        HOUSEHOLD_MOVED = 3, 'Household Moved'
        HOUSEHOLD_ABSENT = 4, 'Household Absent'
        HOUSE_DESTROYED = 5, 'House Destroyed'

    class ConsentType(models.IntegerChoices):
        YES = 1, 'Yes'
        NO = 2, 'No'
        HOUSEHOLD_MOVED = 3, 'Household Moved'
        HOUSEHOLD_ABSENT = 4, 'Household Absent'
        HOUSE_DESTROYED = 5, 'House Destroyed'

    class ResPhonePossType(models.IntegerChoices):
        YES = 1, 'Yes'
        NO = 2, 'No'
        RESPONDENT_HEAD = 5, 'Respondent is the Head of Household'

    class PhoneAllowType(models.IntegerChoices):
        YES = 1, 'Yes'
        NO_CANNOT_GIVE = 2, 'No, I cannot give it to you'
        DONT_KNOW = 3, 'Don\'t know'

    cluster = models.ForeignKey(
        'Cluster',
        related_name='households',
        null=False,
        on_delete=models.RESTRICT,
        help_text='Foreign key to the Cluster.'
    )

    area = models.ForeignKey(
        'Area',
        related_name='households',
        null=False,
        on_delete=models.RESTRICT,
        help_text='Foreign key to the Area.'
    )

    event_staff = models.ForeignKey(
        'Staff',
        related_name='households',
        null=False,
        on_delete=models.RESTRICT,
        help_text='Foreign key to the Staff.'
    )

    key = models.CharField(max_length=80, null=False, unique=True)
    submission_date = models.DateField(blank=True, null=True)
    interview_date = models.DateField(blank=True, null=True)
    cluster_code = models.CharField(max_length=255, blank=True, null=True)
    area_code = models.CharField(max_length=255, blank=True, null=True)
    staff_code = models.CharField(max_length=255, blank=True, null=True)
    met_status = models.IntegerField(choices=MetStatusType.choices, blank=True, null=True)
    consent = models.IntegerField(choices=ConsentType.choices, blank=True, null=True)
    household_code = models.CharField(max_length=255, blank=True, null=True)
    household_address = models.CharField(max_length=255, blank=True, null=True)
    household_head_name = models.CharField(max_length=255, blank=True, null=True)

    gps_latitude = models.DecimalField(max_digits=38, decimal_places=10, blank=True, null=True)
    gps_longitude = models.DecimalField(max_digits=38, decimal_places=10, blank=True, null=True)
    gps_altitude = models.DecimalField(max_digits=38, decimal_places=10, blank=True, null=True)
    gps_accuracy = models.DecimalField(max_digits=38, decimal_places=10, blank=True, null=True)

    respondent_name = models.CharField(max_length=255, blank=True, null=True)
    residence_count = models.CharField(max_length=255, blank=True, null=True)
    visitor_count = models.CharField(max_length=255, blank=True, null=True)
    rep_member_count = models.CharField(max_length=255, blank=True, null=True)

    # contact info
    head_phone_cell = models.IntegerField(choices=YesNoType.choices, blank=True, null=True)
    head_phone_allow = models.IntegerField(choices=PhoneAllowType.choices, blank=True, null=True)
    head_phone = models.CharField(max_length=255, blank=True, null=True)
    head_phone_confirm = models.CharField(max_length=255, blank=True, null=True)
    res_phone_cell = models.IntegerField(choices=ResPhonePossType.choices, blank=True, null=True)
    res_phone_allow = models.IntegerField(choices=PhoneAllowType.choices, blank=True, null=True)
    res_phone = models.CharField(max_length=255, blank=True, null=True)
    res_phone_confirm = models.CharField(max_length=255, blank=True, null=True)
    any_phone_cell = models.IntegerField(choices=YesNoType.choices, blank=True, null=True)
    any_phone_allow = models.IntegerField(choices=PhoneAllowType.choices, blank=True, null=True)
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
        db_table = 'households'

    def __str__(self):
        return f"{self.household_head_name} - {self.household_code} ({self.id})"


@db_timestamps
class HouseholdMember(QueryExtensionMixin, models.Model):
    class MemberType(models.IntegerChoices):
        RESIDENT = 1, 'Resident'
        VISITOR = 2, 'Visitor'

    class SexType(models.IntegerChoices):
        MALE = 1, 'Male'
        FEMALE = 2, 'Female'

    class RelationHeadType(models.IntegerChoices):
        HEAD = 1, 'Head'
        SPOUSE = 2, 'Spouse'
        BIOLOGICAL_CHILD = 3, 'Biological Child'
        FATHER_MOTHER = 4, 'Father/Mother'
        NONBIOLOGICAL_CHILD = 5, 'Non-Biological Child'
        ADOPTED_CHILD = 6, 'Adopted Child'
        INLAW = 7, 'Inlaw'
        GRANDCHILD = 8, 'Grandchild'
        OTHER_RELATION = 9, 'Other Relation'
        NO_RELATIONSHIP = 10, 'No Relationship'

    household = models.ForeignKey(
        Household,
        related_name='household_members',
        null=False,
        on_delete=models.CASCADE,
        help_text='Foreign key to parent Household.'
    )
    key = models.CharField(max_length=80, null=False, unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    member_type = models.IntegerField(choices=MemberType.choices, blank=True, null=True)
    sex = models.IntegerField(choices=SexType.choices, blank=True, null=True)
    age_in_years = models.IntegerField(blank=True, null=True)
    rel_head = models.IntegerField(choices=RelationHeadType.choices, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'household_members'

    def __str__(self):
        return f"{self.full_name} ({self.id})"
