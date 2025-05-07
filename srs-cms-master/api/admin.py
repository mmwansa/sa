import os.path
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.management import call_command
from django.utils.safestring import mark_safe
from api.models import *
from api.odk.importers.form_submissions.form_submission_importer import FromSubmissionImporter
from api.odk.exporters.entity_lists.entity_list_exporter import EntityListExporter
from .forms import AdminImportFileForm
import html
import traceback
import tempfile
import io
import re


def get_admin_changelist_url(model_class):
    return reverse(f"admin:{model_class._meta.app_label}_{model_class._meta.model_name}_changelist")


class AdminImportFileBaseAdmin(admin.ModelAdmin):
    def __init__(self, model, admin_site, import_command=None, import_kwargs=None):
        self.__import_command = import_command
        self.__import_kwargs = import_kwargs or {}
        super().__init__(model, admin_site)

    change_list_template = "admin/import_file_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        model = self.model
        app_label = model._meta.app_label
        model_name = model._meta.model_name

        custom_urls = [
            path(
                "import-file/",
                self.admin_site.admin_view(self.import_file),
                name=f"{app_label}_{model_name}_import_file",
            ),
        ]
        return custom_urls + urls

    def __strip_ansi_codes(self, text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def __format_command_output(self, stdout, stderr):
        output = self.__strip_ansi_codes(stdout.getvalue().strip())
        error = self.__strip_ansi_codes(stderr.getvalue().strip())

        output = mark_safe(html.escape(output).replace('\n', '<br>'))
        error_output = mark_safe(html.escape(error).replace('\n', '<br>'))
        return output, error_output

    def import_file(self, request):
        if request.method == "POST":
            form = AdminImportFileForm(request.POST, request.FILES)
            if form.is_valid():
                import_file = form.cleaned_data['file']
                try:
                    with tempfile.NamedTemporaryFile(suffix=f"_{os.path.basename(import_file.name)}",
                                                     mode="wb",
                                                     delete=False) as temp_file:
                        for chunk in import_file.chunks():
                            temp_file.write(chunk)

                    stdout = io.StringIO()
                    stderr = io.StringIO()
                    call_command(
                        self.__import_command,
                        temp_file.name,
                        stdout=stdout,
                        stderr=stderr,
                        **self.__import_kwargs
                    )
                    output, error_output = self.__format_command_output(stdout, stderr)

                    if output:
                        messages.add_message(request, messages.SUCCESS if not error_output else messages.ERROR, output)
                    if error_output:
                        messages.add_message(request, messages.ERROR, error_output)

                    if os.path.exists(temp_file.name):
                        os.remove(temp_file.name)

                    return redirect(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist")
                except Exception as ex:
                    ex_trace = traceback.format_exc()
                    self.message_user(request, f"Error: {ex_trace}", level=messages.ERROR)
        else:
            form = AdminImportFileForm()

        return render(
            request,
            "admin/import_file_form.html",
            {
                "form": form,
                "title": f"Import {self.model._meta.verbose_name_plural}"
            }
        )


@admin.register(User)
class UserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('provinces',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('provinces',)}),
    )
    list_display = (
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
        "provinces__name",
    )
    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "provinces__name",
        "provinces__code",
    )


# ODK
@admin.register(OdkProject)
class OdkProjectAdmin(AdminImportFileBaseAdmin):
    def __init__(self, model, admin_site):
        super().__init__(
            model,
            admin_site,
            import_command='load_odk_projects',
            import_kwargs={'verbose': True}
        )

    change_form_template = "admin/odk/odk_project/change_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:project_id>/import_form_submissions/',
                self.admin_site.admin_view(self.import_form_submissions),
                name='odk_project_import_form_submissions',
            ),
            path(
                '<int:project_id>/export_entity_lists/',
                self.admin_site.admin_view(self.export_entity_lists),
                name='odk_project_export_entity_lists',
            ),
        ]
        return custom_urls + urls

    def import_form_submissions(self, request, project_id):
        try:
            odk_import_result = FromSubmissionImporter(odk_projects=project_id, ).execute()

            if not odk_import_result.has_errors:
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    mark_safe(
                        f"ODK Import finished successfully.<br>{"<br>".join(odk_import_result.info_log)}"
                    )
                )
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    mark_safe(
                        f"ODK Import finished with errors.<br>{"<br>".join(odk_import_result.info_log)}"
                    )
                )
                messages.add_message(
                    request,
                    messages.ERROR,
                    mark_safe(
                        f"Errors:<br>{"<br>".join(odk_import_result.errors)}"
                    )
                )
        except Exception as e:
            messages.add_message(request, messages.ERROR, f"ODK Import did not finish: {str(e)}")

        return redirect('..')

    def export_entity_lists(self, request, project_id):
        try:
            odk_export_result = EntityListExporter(odk_projects=project_id).execute()

            if not odk_export_result.has_errors:
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    mark_safe(
                        f"ODK Export finished successfully.<br>{"<br>".join(odk_export_result.info_log)}"
                    )
                )
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    mark_safe(
                        f"ODK Export finished with errors.<br>{"<br>".join(odk_export_result.info_log)}"
                    )
                )
                messages.add_message(
                    request,
                    messages.ERROR,
                    mark_safe(
                        f"Errors:<br>{"<br>".join(odk_export_result.errors)}"
                    )
                )
        except Exception as e:
            messages.add_message(request, messages.ERROR, f"ODK Export did not finish: {str(e)}")

        return redirect('..')

    list_display = (
        'id',
        'name',
        'project_id',
    )
    list_filter = (
        'name',
        'project_id',
    )
    search_fields = (
        'name',
        'project_id',
    )


@admin.register(OdkForm)
class OdkFormAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'xml_form_id',
        'version',
        'odk_project__name',
    )
    list_filter = (
        'name',
        'xml_form_id',
        'version',
    )
    search_fields = (
        'name',
        'xml_form_id',
        'version',
    )


@admin.register(OdkFormImporter)
class OdkFormImporterAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'importer',
        'odk_form__name',
        'odk_form__version',
        'etl_document__name',
        'etl_document__version',
    )
    list_filter = (
        'importer',
        'odk_form__name',
        'odk_form__version',
        'etl_document__name',
    )
    search_fields = (
        'importer',
        'odk_form__name',
        'odk_form__version',
    )


@admin.register(OdkFormImporterJob)
class OdkFormImporterJobAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'importer',
        'status',
        'created_at',
        'import_start_date',
        'import_end_date',
        'odk_project_name',
        'odk_form_name',
        'odk_form_version',
    )
    list_filter = (
        'status',
        'created_at',
        'import_start_date',
        'import_end_date',
        'odk_form_importer__importer',
        'odk_form_importer__odk_form__odk_project__name',
    )
    search_fields = (
        'odk_form_importer__importer',
        'status',
        'odk_form_importer__odk_form__odk_project__name',
        'odk_form_importer__odk_form__name',
        'odk_form_importer__odk_form__version',
    )

    def importer(self, odk_form_importer_job):
        return odk_form_importer_job.odk_form_importer.importer

    def odk_form_name(self, odk_form_importer_job):
        return odk_form_importer_job.odk_form_importer.odk_form.name

    def odk_form_version(self, odk_form_importer_job):
        return odk_form_importer_job.odk_form_importer.odk_form.version

    def odk_project_name(self, odk_form_importer_job):
        return odk_form_importer_job.odk_form_importer.odk_form.odk_project.name


@admin.register(OdkEntityList)
class OdkEntityListAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'odk_project__name',
    )
    list_filter = (
        'name',
        'odk_project__name',
    )
    search_fields = (
        'name',
    )


@admin.register(OdkEntityListExporter)
class OdkEntityListExporterAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'exporter',
        'odk_entity_list__name',
        'etl_document__name',
        'etl_document__version',
    )
    list_filter = (
        'exporter',
        'odk_entity_list__name',
        'etl_document__name',
    )
    search_fields = (
        'exporter',
        'odk_entity_list__name',
    )


@admin.register(OdkEntityListExporterJob)
class OdkEntityListExporterJobAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'exporter',
        'status',
        'export_date',
        'odk_entity_list',
        'odk_project_name',
    )
    list_filter = (
        'odk_entity_list_exporter__exporter',
        'status',
        'export_date',
        'odk_entity_list_exporter__odk_entity_list__name',
        'odk_entity_list_exporter__exporter',
        'odk_entity_list_exporter__odk_entity_list__odk_project__name',
    )
    search_fields = (
        'odk_entity_list_exporter__exporter',
        'odk_entity_list_exporter__odk_entity_list__name',
        'odk_entity_list_exporter__exporter',
        'odk_entity_list_exporter__odk_entity_list__odk_project__name',
    )

    def exporter(self, odk_entity_list_exporter_job):
        return odk_entity_list_exporter_job.odk_entity_list_exporter.exporter

    def odk_entity_list(self, odk_entity_list_exporter_job):
        return odk_entity_list_exporter_job.odk_entity_list_exporter.odk_entity_list.name

    def odk_project_name(self, odk_entity_list_exporter_job):
        return odk_entity_list_exporter_job.odk_entity_list_exporter.odk_entity_list.odk_project.name


# ETL
@admin.register(EtlDocument)
class EtlDocumentAdmin(AdminImportFileBaseAdmin):
    def __init__(self, model, admin_site):
        super().__init__(
            model,
            admin_site,
            import_command='load_etl_documents',
            import_kwargs={'verbose': True}
        )

    list_display = (
        'id',
        'name',
        'version',
    )
    list_filter = (
        'name',
        'version',
    )
    search_fields = (
        'name',
        'version',
    )


@admin.register(EtlMapping)
class EtlMappingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'source_name',
        'target_name',
        'is_enabled',
        'etl_document__name',
        'etl_document__version',
    )
    list_filter = (
        'is_enabled',
        'etl_document__name',
        'etl_document__version',
    )
    search_fields = (
        'source_name',
        'target_name',
        'etl_document__name',
        'etl_document__version',
    )


# Events
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'event_type',
        'interview_date',
        'cluster__name',
        'area_code',
        'cms_status',
    )
    list_filter = (
        'event_type',
        'interview_date',
        'cluster__name',
        'area_code',
        'cms_status',
    )
    search_fields = (
        'key',
        'cluster__name',
        'area_code',
    )


@admin.register(Baby)
class BabyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
    )
    list_filter = (
    )
    search_fields = (
        'key',
        'name',
    )


@admin.register(Death)
class DeathAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'death_type',
        'death_code',
        'death_status',
        'va_proposed_date',
        'va_scheduled_date',
        'va_completed_date',
        'va_staff',
    )
    list_filter = (
        'death_type',
        'death_status',
        'va_proposed_date',
        'va_scheduled_date',
        'va_completed_date',
    )
    search_fields = (
        'key',
        'death_code',
        'deceased_name',
        'va_staff__code',
        'va_staff__full_name',
        'va_staff__email',
    )


# Households
@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'household_code',
        'interview_date',
        'cluster__name',
        'area__code',
        'event_staff__full_name',
        'cms_status',
    )
    list_filter = (
        'interview_date',
        'cluster__name',
        'cms_status',
    )
    search_fields = (
        'key',
        'household_code',
        'respondent_name',
        'cluster__name',
        'area__code',
        'event_staff__full_name',
    )


@admin.register(HouseholdMember)
class HouseholdMemberAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'member_type',
        'full_name',
        'sex',
        'household',
    )
    list_filter = (
        'member_type',
        'sex',
    )
    search_fields = (
        'key',
        'full_name',
    )


# Verbal Autopsies
@admin.register(VerbalAutopsy)
class VerbalAutopsyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'submission_date',
        'cluster__name',
        'area__code',
        'death',
    )
    list_filter = (
        'submission_date',
    )
    search_fields = (
        'key',
        'death__death_code',
        'cluster__name',
        'area__code',
    )


@admin.register(Province)
class ProvinceAdmin(AdminImportFileBaseAdmin):
    def __init__(self, model, admin_site):
        super().__init__(
            model,
            admin_site,
            import_command='load_provinces',
            import_kwargs={'verbose': True},
        )

    list_display = (
        'id',
        'code',
        'name',
    )
    list_filter = (

    )
    search_fields = (
        'code',
        'name',
    )


@admin.register(Cluster)
class ClusterAdmin(AdminImportFileBaseAdmin):
    def __init__(self, model, admin_site):
        super().__init__(
            model,
            admin_site,
            import_command='load_clusters',
            import_kwargs={'verbose': True},
        )

    list_display = (
        'id',
        'code',
        'name',
        'province__name',
    )
    list_filter = (
        'province__name',
    )
    search_fields = (
        'code',
        'name',
        'province__name',
    )


@admin.register(Area)
class AreaAdmin(AdminImportFileBaseAdmin):
    def __init__(self, model, admin_site):
        super().__init__(
            model,
            admin_site,
            import_command='load_areas',
            import_kwargs={'verbose': True},
        )

    list_display = (
        'id',
        'code',
    )
    list_filter = (

    )
    search_fields = (
        'code',
        'adm0_code',
        'adm0_name',
        'adm1_code',
        'adm1_name',
        'adm2_code',
        'adm2_name',
        'adm3_code',
        'adm3_name',
        'adm4_code',
        'adm4_name',
        'adm5_code',
        'adm5_name',
    )


@admin.register(Staff)
class StaffAdmin(AdminImportFileBaseAdmin):
    def __init__(self, model, admin_site):
        super().__init__(
            model,
            admin_site,
            import_command='load_staff',
            import_kwargs={'verbose': True},
        )

    list_display = (
        'id',
        'code',
        'staff_type',
        'full_name',
        'cms_status',
        'province__name',
        'cluster__name',
    )
    list_filter = (
        'staff_type',
        'cms_status',
        'province__name',
    )
    search_fields = (
        'code',
        'full_name',
        'province__name',
        'cluster__name',
    )
