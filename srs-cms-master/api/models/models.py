from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.db.models import Q, CheckConstraint
from api.models.decorators import db_timestamps
from api.models.query_extensions import QueryExtensionMixin
from api.odk.importers.form_submissions.form_submission_importer_factory import FromSubmissionImporterFactory
from api.odk.exporters.entity_lists.entity_list_exporter_factory import EntityListExporterFactory
from api.odk.transformers import TransformField
from api.common import Utils, TypeCaster, Permissions
from django.contrib.auth.models import AbstractUser


@db_timestamps
class User(QueryExtensionMixin, AbstractUser):
    provinces = models.ManyToManyField('Province', blank=True, related_name='assigned_users')

    class Meta:
        db_table = 'users'


@db_timestamps
class EtlDocument(QueryExtensionMixin, models.Model):
    name = models.TextField(
        null=False,
        help_text='Name of the project. Does not need to match the name in ODK.',
        verbose_name='ETL Document Name',
    )
    version = models.CharField(
        max_length=255,
        null=False,
        help_text='The ODK Form Version this document supports.',
        verbose_name='ETL Document Version',
    )
    source_root = models.CharField(
        max_length=255,
        null=True,
        help_text='Path to root object to ETL. If null the document will be used as root.'
    )

    class Meta:
        managed = True
        db_table = 'etl_documents'

    def __str__(self):
        return f"{self.name} - {self.version} ({self.id})"


@db_timestamps
class EtlMapping(QueryExtensionMixin, models.Model):
    etl_document = models.ForeignKey(
        EtlDocument,
        related_name='etl_mappings',
        null=False,
        on_delete=models.CASCADE,
        help_text='Foreign key to parent ODK Project.'
    )
    source_name = models.CharField(
        max_length=255,
        null=False,
        help_text='Name of the field in the incoming data.'
    )
    target_name = models.CharField(
        max_length=255,
        null=False,
        help_text='Field name of the target table.'
    )
    target_type = models.CharField(
        max_length=255,
        null=False,
        choices=TypeCaster.TypeCode.choices,
        help_text='Data type for the target table column value.'
    )
    default = models.CharField(
        max_length=255,
        null=True,
        help_text='Default value for the target table column value if the source value is falsey.'
    )
    transform = models.JSONField(
        null=True,
        help_text='Transformer configuration for this field.'
    )
    is_primary_key = models.BooleanField(
        default=False,
        help_text='This field is a primary key in the srs-cms database.'
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text='Enable/Disable this field from being imported.'
    )
    is_required = models.BooleanField(
        default=True,
        help_text='If true this will raise an error if the source_name is not in the ODK data record being imported, otherwise import the field if it exists or set it to null.'
    )

    class Meta:
        managed = True
        db_table = 'etl_mappings'
        constraints = [
            models.UniqueConstraint(fields=['etl_document', 'source_name'],
                                    name='unique_etl_mappings_etl_document_source_name'),
            models.UniqueConstraint(fields=['etl_document', 'target_name'],
                                    name='unique_etl_mappings_etl_document_target_name'),
            models.UniqueConstraint(fields=['etl_document', 'source_name', 'target_name'],
                                    name='unique_etl_mappings_etl_document_source_name_target_name')
        ]

    def __str__(self):
        return f"{self.etl_document.name}: {self.source_name} ({self.id})"

    def get_target_value(self, obj, cast=False, transform=False):
        value = Utils.get_field(obj, self.source_name, default=self.default)
        if cast:
            value = self.cast_value(value)
        if transform:
            value = self.transform_value(value)
        return value

    def cast_value(self, value, transform=False):
        value = TypeCaster.cast(value, self.target_type, default=self.default)
        if transform:
            value = self.transform_value(value)
        return value

    def transform_value(self, value):
        if self.transform:
            value = TransformField.get(self.transform).transform(value)
        return value

    def has_source_name(self, obj):
        return Utils.has_field(obj, self.source_name)


@db_timestamps
class OdkProject(QueryExtensionMixin, models.Model):
    name = models.TextField(
        null=False,
        help_text='Name of the project. Does not need to match the name in ODK.',
        verbose_name='Project Name'
    )
    project_id = models.IntegerField(
        null=False,
        help_text='ODK Project ID.'
    )
    is_enabled = models.BooleanField(
        default=False,
        help_text='Enable/Disable this project for importing.'
    )

    class Meta:
        managed = True
        db_table = 'odk_projects'

    def __str__(self):
        return f"{self.name} ({self.id})"


@db_timestamps
class OdkForm(QueryExtensionMixin, models.Model):
    odk_project = models.ForeignKey(
        OdkProject,
        related_name='odk_forms',
        null=False,
        on_delete=models.CASCADE,
        help_text='Foreign key to parent ODK Project.'
    )
    name = models.TextField(
        null=False,
        help_text='Name of the form. Does not need to match the name in ODK.',
        verbose_name='ODK Form Name'
    )
    xml_form_id = models.CharField(
        max_length=255,
        null=False,
        help_text='ODK XML Form ID.',
        verbose_name='ODK Form XML Form ID'
    )
    version = models.CharField(
        max_length=255,
        null=False,
        help_text='The ODK Form Version to import.',
        verbose_name='ODK Form Version'
    )
    is_enabled = models.BooleanField(
        default=False,
        help_text='Enable/Disable this form for importing.',
        verbose_name='ODK Form Is Enabled'
    )

    class Meta:
        managed = True
        db_table = 'odk_forms'
        constraints = [models.UniqueConstraint(fields=['odk_project', 'xml_form_id', 'version'],
                                               name='unique_odk_forms_odk_project_xml_form_id_version')]

    def __str__(self):
        return f"{self.odk_project.name}: {self.name} ({self.id})"

    def get_odk_form_importers(self, enabled=True, importers=None):
        importers = Utils.to_list(importers)
        filter_args = {'is_enabled': enabled}
        if importers:
            filter_args['importer__in'] = importers
        return list(self.odk_form_importers.filter(**filter_args).order_by('import_order'))

    def get_odk_form_importer(self, importer, enabled=True):
        importer = (self.get_odk_form_importers(enabled=enabled, importers=importer)[0:1] or [None])[0]
        return importer

    def get_primary_odk_form_importer(self, _importer_list: None):
        if _importer_list is not None:
            importers = Utils.to_list(_importer_list)
        else:
            importers = self.get_odk_form_importers()

        primary_importer = min(importers, key=lambda importer: importer.import_order, default=None)
        return primary_importer

    def get_child_odk_form_importers(self, _importer_list: None):
        if _importer_list is not None:
            importers = Utils.to_list(_importer_list)
        else:
            importers = self.get_odk_form_importers()

        primary_importer = self.get_primary_odk_form_importer(_importer_list=importers)
        child_importers = list(filter(lambda importer: importer != primary_importer, importers))
        return child_importers


@db_timestamps
class OdkFormImporter(QueryExtensionMixin, models.Model):
    odk_form = models.ForeignKey(
        OdkForm,
        related_name='odk_form_importers',
        null=False,
        on_delete=models.CASCADE,
        help_text='Foreign key to parent ODK Form.'
    )
    etl_document = models.ForeignKey(
        EtlDocument,
        related_name='odk_form_importers',
        null=True,
        on_delete=models.SET_NULL,
        help_text='Foreign key to the ETL Document.'
    )
    import_order = models.IntegerField(null=False,
                                       help_text='The order to execute the importers. The first importer is always the primary importer and the remaining are children.')
    importer = models.CharField(
        max_length=255,
        null=False,
        choices=FromSubmissionImporterFactory.ODK_IMPORTERS_CHOICES,
        help_text='Importer class for the form.')
    is_enabled = models.BooleanField(
        default=False,
        help_text='Enable/Disable this importer.'
    )

    class Meta:
        managed = True
        db_table = 'odk_form_importers'
        ordering = ['import_order']
        constraints = [models.UniqueConstraint(fields=['odk_form', 'importer'],
                                               name='unique_odk_form_importers_odk_form_importer'),
                       models.UniqueConstraint(fields=['odk_form', 'import_order'],
                                               name='unique_odk_form_importers_odk_form_import_order')
                       ]

    def __str__(self):
        return f"{self.odk_form.name}: {self.importer} ({self.id})"


@db_timestamps
class OdkFormImporterJob(QueryExtensionMixin, models.Model):
    STATUS_RUNNING = 'RUNNING'
    STATUS_SUCCESSFUL = 'SUCCESSFUL'
    STATUS_ERRORED = 'ERRORED'

    STATUS_CHOICES = [
        (STATUS_RUNNING, 'Running'),
        (STATUS_SUCCESSFUL, 'Successful'),
        (STATUS_ERRORED, 'Errored'),
    ]

    odk_form_importer = models.ForeignKey(
        OdkFormImporter,
        related_name='odk_form_importer_jobs',
        null=False,
        on_delete=models.CASCADE,
        help_text='Foreign key to ODK Form Importer.'
    )
    import_start_date = models.DateTimeField(null=False, blank=False,
                                             help_text="The form submission start date and time this importer last loaded.")
    import_end_date = models.DateTimeField(null=True, blank=False,
                                           help_text="The form submission end date and time this importer last loaded.")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        null=False,
        blank=False,
        help_text="Status of the importer."
    )
    args = models.JSONField(null=True, blank=True, help_text="Arguments for the import process.")
    result = models.JSONField(null=True, blank=True, help_text="Result of the import process.")

    class Meta:
        db_table = 'odk_form_importer_jobs'

    def __str__(self):
        return f"{self.odk_form_importer.importer} ({self.id})"


@db_timestamps
class OdkEntityList(QueryExtensionMixin, models.Model):
    odk_project = models.ForeignKey(
        OdkProject,
        related_name='odk_entity_lists',
        null=False,
        on_delete=models.CASCADE,
        help_text='Foreign key to parent ODK Project.'
    )
    name = models.CharField(
        max_length=255,
        null=False,
        help_text='Name of the ODK Entity List. Must match the ODK Entity List name.',
        verbose_name='ODK Entity List Name'
    )
    is_enabled = models.BooleanField(
        default=False,
        help_text='Enable/Disable this Entity List from exporting.'
    )

    class Meta:
        managed = True
        db_table = 'odk_entity_lists'
        constraints = [models.UniqueConstraint(fields=['odk_project', 'name'],
                                               name='unique_odk_entity_lists_odk_project_name')]

    def get_odk_entity_list_exporters(self, enabled=True, exporters=None):
        exporters = Utils.to_list(exporters)
        filter_args = {'is_enabled': enabled}
        if exporters:
            filter_args['exporter__in'] = exporters
        return list(self.odk_entity_list_exporters.filter(**filter_args).order_by('id'))

    def get_odk_entity_list_exporter(self, exporter, enabled=True):
        exporter = (self.odk_entity_list_exporters(enabled=enabled, exporters=exporter)[0:1] or None)[0]
        return exporter

    def __str__(self):
        return f"{self.odk_project.name}: {self.name} ({self.id})"


@db_timestamps
class OdkEntityListExporter(QueryExtensionMixin, models.Model):
    odk_entity_list = models.ForeignKey(
        OdkEntityList,
        related_name='odk_entity_list_exporters',
        null=False,
        on_delete=models.CASCADE,
        help_text='Foreign key to parent ODK Entity List.'
    )
    etl_document = models.ForeignKey(
        EtlDocument,
        related_name='odk_entity_list_exporters',
        null=True,
        on_delete=models.SET_NULL,
        help_text='Foreign key to the ETL Document.'
    )
    exporter = models.CharField(
        max_length=255,
        null=False,
        choices=EntityListExporterFactory.ODK_EXPORTERS_CHOICES,
        help_text='Exporter class for the Entity List.')
    is_enabled = models.BooleanField(
        default=False,
        help_text='Enable/Disable this exporter.'
    )

    class Meta:
        managed = True
        db_table = 'odk_entity_list_exporters'
        constraints = [models.UniqueConstraint(fields=['odk_entity_list', 'exporter'],
                                               name='unique_odk_entity_list_exporters_odk_entity_list_exporter')
                       ]

    def __str__(self):
        return f"{self.odk_entity_list.name}: {self.exporter} ({self.id})"


@db_timestamps
class OdkEntityListExporterJob(QueryExtensionMixin, models.Model):
    STATUS_RUNNING = 'RUNNING'
    STATUS_SUCCESSFUL = 'SUCCESSFUL'
    STATUS_ERRORED = 'ERRORED'

    STATUS_CHOICES = [
        (STATUS_RUNNING, 'Running'),
        (STATUS_SUCCESSFUL, 'Successful'),
        (STATUS_ERRORED, 'Errored'),
    ]

    odk_entity_list_exporter = models.ForeignKey(
        OdkEntityListExporter,
        related_name='odk_entity_list_exporter_jobs',
        null=False,
        on_delete=models.CASCADE,
        help_text='Foreign key to ODK Entity List Exporter.'
    )

    export_date = models.DateTimeField(null=False, blank=False, help_text="The date/time this exporter last ran.")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        null=False,
        blank=False,
        help_text="Status of the export."
    )
    args = models.JSONField(null=True, blank=True, help_text="Arguments for the export process.")
    result = models.JSONField(null=True, blank=True, help_text="Result of the export process.")

    class Meta:
        db_table = 'odk_entity_list_exporter_jobs'

    def __str__(self):
        return f"{self.odk_entity_list_exporter.exporter}: {self.status} ({self.id})"


class ProvinceManager(models.Manager):
    def for_user(self, user):
        """
        Returns provinces the user is allowed to view.
        """
        if user.is_superuser or Permissions.has_permission(user, Permissions.Codes.VIEW_ALL_PROVINCES):
            return self.all()
        elif Permissions.has_permission(user, Permissions.Codes.VIEW_ASSIGNED_PROVINCES):
            return self.filter(id__in=user.provinces.values_list('id', flat=True))
        else:
            return self.none()


@db_timestamps
class Province(QueryExtensionMixin, models.Model):
    code = models.CharField(max_length=2, blank=False, null=False, verbose_name='Province Code')
    name = models.CharField(max_length=100, blank=False, null=False, verbose_name='Province Name')

    objects = ProvinceManager()

    class Meta:
        managed = True
        db_table = 'provinces'
        indexes = [
            # For text search.
            GinIndex(fields=['code'], name='provinces_gin_code', opclasses=['gin_trgm_ops'])
        ]

    def __str__(self):
        return f"{self.code} - {self.name} ({self.id})"


@db_timestamps
class Cluster(QueryExtensionMixin, models.Model):
    province = models.ForeignKey(
        'Province',
        related_name='clusters',
        null=False,
        on_delete=models.RESTRICT,
        help_text='Foreign key to the Province.'
    )

    code = models.CharField(max_length=12, null=False, unique=True, verbose_name='Cluster Code')
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cluster Name')

    class Meta:
        managed = True
        db_table = 'clusters'
        indexes = [
            # For text search.
            GinIndex(fields=['code'], name='clusters_gin_code', opclasses=['gin_trgm_ops'])
        ]

    def __str__(self):
        return f"{self.province.name}: {self.code} - {self.name} ({self.id})"


@db_timestamps
class Staff(QueryExtensionMixin, models.Model):
    class CmsStatusType(models.IntegerChoices):
        """
        Does not come from ODK. Used by the system/admins.
        """
        NORMAL = 1, 'Normal'
        DUPLICATE = 2, 'Duplicate'

    class StaffType(models.TextChoices):
        CSA = 'CSA', 'Community Surveillance Assistant'
        VA = 'VA', 'Verbal Autopsy Interviewer'

    cluster = models.ForeignKey(
        Cluster,
        related_name='staff',
        null=True,
        on_delete=models.SET_NULL,
        help_text='Foreign key to the Cluster.'
    )
    province = models.ForeignKey(
        Province,
        related_name='staff',
        null=True,
        on_delete=models.SET_NULL,
        help_text='Foreign key to the Province.'
    )

    code = models.CharField(max_length=12, blank=True, null=True, verbose_name='Staff Code')
    staff_type = models.CharField(max_length=12, choices=StaffType.choices, blank=False, null=False,
                                  verbose_name='Staff Type')
    full_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Staff Full Name')
    title = models.CharField(max_length=100, blank=True, null=True)
    mobile_per = models.CharField(max_length=9, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    cms_status = models.IntegerField(choices=CmsStatusType.choices, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'staff'
        verbose_name_plural = 'Staff'
        indexes = [
            # For text search.
            GinIndex(fields=['code'], name='staff_gin_code', opclasses=['gin_trgm_ops'])
        ]

        # staff_type=CSA must have a cluster
        # staff_type=VA must have a province
        constraints = [
            CheckConstraint(
                condition=(
                        Q(staff_type="CSA", cluster__isnull=False) | Q(staff_type="VA", province__isnull=False)
                ),
                name="check_staff_type_fks"
            )
        ]

    def __str__(self):
        return f"{self.code} - {self.full_name} ({self.id})"


@db_timestamps
class Area(QueryExtensionMixin, models.Model):
    cluster = models.ForeignKey(
        Cluster,
        related_name='areas',
        null=False,
        on_delete=models.RESTRICT,
        help_text='Foreign key to the Cluster.'
    )
    code = models.CharField(max_length=12, null=False, unique=True)
    # TODO: Is this needed? Do we need a foreign key to the province?
    #  The adm1 level data is province level
    #  This is probably redundant here, but we may need to query this table by province.
    province_code = models.CharField(max_length=20, blank=True, null=True)
    adm0_code = models.CharField(max_length=20, blank=True, null=True)
    adm0_name = models.CharField(max_length=100, blank=True, null=True)
    adm1_code = models.CharField(max_length=20, blank=True, null=True)
    adm1_name = models.CharField(max_length=100, blank=True, null=True)
    adm2_code = models.CharField(max_length=20, blank=True, null=True)
    adm2_name = models.CharField(max_length=100, blank=True, null=True)
    adm3_code = models.CharField(max_length=20, blank=True, null=True)
    adm3_name = models.CharField(max_length=100, blank=True, null=True)
    adm4_code = models.CharField(max_length=20, blank=True, null=True)
    adm4_name = models.CharField(max_length=100, blank=True, null=True)
    adm5_code = models.CharField(max_length=20, blank=True, null=True)
    adm5_name = models.CharField(max_length=100, blank=True, null=True)
    urban_rural = models.CharField(max_length=20, blank=True, null=True)
    carto_house_count = models.IntegerField(blank=True, null=True)
    carto_pop_count = models.IntegerField(blank=True, null=True)
    import_code = models.CharField(max_length=20, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'areas'
        indexes = [
            # For text search.
            GinIndex(fields=['code'], name='areas_gin_code', opclasses=['gin_trgm_ops'])
        ]

    def __str__(self):
        return f"{self.cluster.code} - {self.code} ({self.id})"

# Disabled - For future use.
# @db_timestamps
# class Mobile(QueryExtensionMixin, models.Model):
#     class CmsStatusType(models.TextChoices):
#         """
#         Does not come from ODK. Used by the system/admins.
#         """
#         NORMAL = '1', 'Normal'
#         DUPLICATE = '2', 'Duplicate'
#     staff = models.ForeignKey(
#         Staff,
#         related_name='mobile_staff',
#         null=True,
#         on_delete=models.SET_NULL,
#         help_text='Foreign key to the Staff.'
#     )
#
#     phone_number = models.CharField(max_length=12, blank=True, null=True)
#     imei = models.CharField(max_length=15, blank=True, null=True)
#     model_name = models.CharField(max_length=50, blank=True, null=True)
#     model_number = models.CharField(max_length=50, blank=True, null=True)
#     serial_number = models.CharField(max_length=50, blank=True, null=True)
#     staff_code = models.CharField(max_length=12, blank=True, null=True)
#     cms_status = models.IntegerField(choices=CmsStatusType.choices, null=True)
#     comment = models.CharField(max_length=255, blank=True, null=True)
#     created_by = models.IntegerField(blank=True, null=True)
#     updated_by = models.IntegerField(blank=True, null=True)
#
#     class Meta:
#         managed = True
#         db_table = 'mobiles'
