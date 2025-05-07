import factory
import uuid
import itertools
import string
import random
from datetime import datetime
from django.db.models import Max
from api.models import (OdkProject, OdkForm, EtlDocument, EtlMapping,
                        Province, Cluster, Area, Staff,
                        Event, Death, Baby,
                        Household, HouseholdMember,
                        VerbalAutopsy,
                        OdkFormImporter)
from api.common import Utils, TypeCaster
from api.dev.seeds.seed_loader import SeedLoader
from api.odk.importers.form_submissions.form_submission_importer_factory import FromSubmissionImporterFactory
from faker import Faker

fake = Faker()


class EtlDocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EtlDocument

    name = 'ETL Doc {}'.format(uuid.uuid4())
    version = 'v{}'.format(uuid.uuid4())
    source_root = None

    @factory.post_generation
    def with_mappings(self, create, with_mappings, **kwargs):
        """Create the ETL Mappings"""
        if not create:
            return

        importer = kwargs.pop('importer', None)
        if with_mappings:
            if importer == FromSubmissionImporterFactory.ODK_EVENTS_IMPORTER_NAME:
                etl_mapping_filename = 'etl_mappings_events.json'
            elif importer == FromSubmissionImporterFactory.ODK_DEATHS_IMPORTER_NAME:
                etl_mapping_filename = 'etl_mappings_deaths.json'
            elif importer == FromSubmissionImporterFactory.ODK_BABIES_IMPORTER_NAME:
                etl_mapping_filename = 'etl_mappings_babies.json'
            elif importer == FromSubmissionImporterFactory.ODK_HOUSEHOLDS_IMPORTER_NAME:
                etl_mapping_filename = 'etl_mappings_households.json'
            elif importer == FromSubmissionImporterFactory.ODK_HOUSEHOLD_MEMBERS_IMPORTER_NAME:
                etl_mapping_filename = 'etl_mappings_household_members.json'
            elif importer == FromSubmissionImporterFactory.ODK_VERBALAUTOPSY_IMPORTER_NAME:
                etl_mapping_filename = 'etl_mappings_verbal_autopsies.json'
            else:
                raise Exception('Unknown importer: {}'.format(importer))
            SeedLoader('test').load_etl_mappings(etl_mapping_filename, self.id)
        self.refresh_from_db()


class EtlMappingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EtlMapping

    etl_document = factory.SubFactory(EtlDocumentFactory)
    source_name = '__id'
    target_name = 'uri'
    target_type = 'str'
    transform = None
    is_enabled = True


class OdkProjectFactory(factory.django.DjangoModelFactory):
    ODK_FORM_NAME_FOR_EVENTS = 'Events'
    ODK_FORM_NAME_FOR_HOUSEHOLDS = 'Households'
    ODK_FORM_NAME_FOR_VERBAL_AUTOPSIES = 'Verbal Autopsies'

    class Meta:
        model = OdkProject
        exclude = ("ODK_FORM_NAME_FOR_EVENTS", "ODK_FORM_NAME_FOR_HOUSEHOLDS", "ODK_FORM_NAME_FOR_VERBAL_AUTOPSIES")

    name = 'ODK Project {}'.format(uuid.uuid4())
    project_id = factory.Sequence(lambda n: n)
    is_enabled = True

    @factory.post_generation
    def with_forms(self, create, with_forms, **kwargs):
        """Create OdkForms for the project."""
        if not create:
            return

        importers = kwargs.pop('importers', [])
        with_etl = kwargs.pop('with_etl', False)
        if with_forms:
            # Events
            all_event_importer_names = (
                list(map(lambda i: i[1], FromSubmissionImporterFactory.ODK_EVENT_IMPORTERS)))

            if isinstance(importers, bool):
                event_importers = all_event_importer_names
            else:
                event_importers = list(filter(lambda i: i in all_event_importer_names, importers))

            create_event_importers = len(event_importers) > 0
            OdkFormFactory.create(odk_project=self,
                                  name=OdkProjectFactory.ODK_FORM_NAME_FOR_EVENTS,
                                  xml_form_id='test-events',
                                  with_importer=create_event_importers,
                                  with_importer__importer=event_importers,
                                  with_importer__with_etl=with_etl)
            # Households
            all_household_importer_names = list(
                map(lambda i: i[1], FromSubmissionImporterFactory.ODK_HOUSEHOLD_IMPORTERS))

            if isinstance(importers, bool):
                household_importers = all_household_importer_names
            else:
                household_importers = list(filter(lambda i: i in all_household_importer_names, importers))

            create_household_importers = len(household_importers) > 0
            OdkFormFactory.create(odk_project=self,
                                  name=OdkProjectFactory.ODK_FORM_NAME_FOR_HOUSEHOLDS,
                                  xml_form_id='test-households',
                                  with_importer=create_household_importers,
                                  with_importer__importer=household_importers,
                                  with_importer__with_etl=with_etl)

            # Verbal Autopsies
            all_va_importer_names = (
                list(map(lambda i: i[1], FromSubmissionImporterFactory.ODK_VERBAL_AUTOPSY_IMPORTERS)))

            if isinstance(importers, bool):
                va_importers = all_va_importer_names
            else:
                va_importers = list(filter(lambda i: i in all_va_importer_names, importers))

            create_va_importers = len(va_importers) > 0
            OdkFormFactory.create(odk_project=self,
                                  name=OdkProjectFactory.ODK_FORM_NAME_FOR_VERBAL_AUTOPSIES,
                                  xml_form_id='test-verbal-autopsies',
                                  with_importer=create_va_importers,
                                  with_importer__importer=va_importers,
                                  with_importer__with_etl=with_etl)


class OdkFormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OdkForm

    odk_project = factory.SubFactory(OdkProjectFactory)
    name = 'ODK Form {}'.format(uuid.uuid4())
    xml_form_id = 'FORM_1'
    version = '1'
    is_enabled = True

    @factory.post_generation
    def with_importer(self, create, with_importer, **kwargs):
        """Create OdkFormImporters for the form."""
        if not create:
            return

        importers = Utils.to_list(kwargs.pop('importer', []))
        with_etl = kwargs.pop('with_etl', False)
        if with_importer:
            for importer in importers:
                etl_document = None
                if with_etl:
                    etl_document = EtlDocumentFactory.create(name=importer,
                                                             version="1",
                                                             with_mappings=True,
                                                             with_mappings__importer=importer)
                odk_form_importer = OdkFormImporterFactory(odk_form=self,
                                                           etl_document=etl_document,
                                                           importer=importer)


class OdkFormImporterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OdkFormImporter

    odk_form = factory.SubFactory(OdkFormFactory)
    etl_document = None
    importer = None
    import_order = factory.LazyAttribute(
        lambda odk_form_importer: (odk_form_importer.odk_form.odk_form_importers.aggregate(
            max_order=Max('import_order')
        )['max_order'] or 0) + 1
    )
    is_enabled = True


class ProvinceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Province

    _codes = [f"{a}{b}" for a, b in itertools.product(string.ascii_uppercase, repeat=2)]
    code = factory.Iterator(_codes)
    name = factory.LazyAttribute(lambda obj: f"Province {obj.code}")

    @factory.post_generation
    def with_clusters(self, create, with_clusters, **kwargs):
        """Create clusters for the province."""
        if not create:
            return

        with_areas = kwargs.pop('with_areas', None)
        with_staff = kwargs.pop('with_staff', None)
        cluster_count = 0
        if with_clusters:
            if isinstance(with_clusters, bool):
                cluster_count = 3
            elif isinstance(with_clusters, int):
                cluster_count = with_clusters

            if cluster_count:
                ClusterFactory.create_batch(cluster_count, province=self, with_areas=with_areas)
                if with_staff:
                    staff_count = 0
                    if isinstance(with_staff, bool):
                        staff_count = 3
                    elif isinstance(with_staff, int):
                        staff_count = with_staff
                    for cluster in self.clusters.all():
                        StaffFactory.create_batch(staff_count, province=self, cluster=cluster)


class ClusterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Cluster

    _codes = [f"{a}{b}" for a, b in itertools.product(string.ascii_uppercase, repeat=2)]
    code = factory.LazyFunction(lambda: f"{random.randint(0, 9999):04d}{random.choice(ClusterFactory._codes)}")
    name = factory.LazyAttribute(lambda obj: f"Cluster {obj.code}")
    province = factory.SubFactory(ProvinceFactory)

    @factory.post_generation
    def with_areas(self, create, with_areas, **kwargs):
        """Create areas for the Cluster."""
        if not create:
            return

        area_count = 0
        if with_areas:
            if isinstance(with_areas, bool):
                area_count = 3
            elif isinstance(with_areas, int):
                area_count = with_areas
            AreaFactory.create_batch(area_count, cluster=self)


class AreaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Area

    _codes = [f"{a}{b}" for a, b in itertools.product(string.ascii_uppercase, repeat=2)]
    code = factory.LazyFunction(lambda: f"{random.choice(AreaFactory._codes)}{random.randint(0, 999):03d}")
    cluster = factory.SubFactory(ClusterFactory)


class StaffFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Staff

    _codes = [f"{a}{b}" for a, b in itertools.product(string.ascii_uppercase, repeat=2)]
    code = factory.LazyFunction(lambda: f"{random.choice(StaffFactory._codes)}{random.randint(0, 999):03d}")
    staff_type = factory.Iterator(map(lambda s: s[0], Staff.StaffType.choices))
    cluster = factory.SubFactory(ClusterFactory)
    province = factory.SubFactory(ProvinceFactory)


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    cluster = factory.SubFactory(ClusterFactory)
    area = factory.SubFactory(AreaFactory)
    event_staff = factory.SubFactory(StaffFactory)
    form_version = "1"
    key = factory.LazyAttribute(lambda o: str(uuid.uuid4()))
    submission_date = None
    event_type = Event.EventType.NO_EVENT
    event_register = Event.EventRegisterType.YES
    consent = Event.ConsentType.GENERAL
    visit_type = Event.VisitType.ROUTINE_VISIT
    consent_type = Event.ConsentType.GENERAL
    visit_method = Event.VisitMethod.HOME_VISIT
    respondent_name = fake.name()
    dec_person_name = fake.name()
    mother_name = fake.name()
    dec_age_val = 1
    # person_age = 1
    event_location = Event.EventLocationType.HOME

    @factory.post_generation
    def for_death(self, create, for_death, **kwargs):
        if not create:
            return
        if for_death:
            # TODO: set death properties
            pass


class DeathFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Death

    event = factory.SubFactory(EventFactory)
    key = factory.LazyAttribute(lambda o: str(uuid.uuid4()))
    death_type = Death.DeathType.NORMAL
    death_code = factory.Sequence(lambda n: n)
    death_status = Death.DeathStatus.NEW_DEATH
    deceased_name = fake.name()
    deceased_sex = Death.SexType.MALE
    deceased_dob = None
    deceased_dod = None
    deceased_age = 1
    deceased_mother_name = fake.name()
    deceased_father_name = fake.name()
    va_key = str(uuid.uuid4())
    va_proposed_date = None


class FormSubmissionFactory(factory.Factory):
    class Meta:
        model = dict

    @classmethod
    def create_event(cls,
                     etl_document,
                     for_death=False,
                     for_baby=False,
                     _province=None, _cluster=None, _area=None, _staff=None, **kwargs):
        if not _province:
            _province = Province.objects.order_by("?").first()
            if not _province:
                _province = ProvinceFactory(with_clusters=True,
                                            with_clusters__with_areas=True,
                                            with_clusters__with_staff=True)
        if not _cluster:
            _cluster = _province.clusters.first()
        if not _area:
            _area = _cluster.areas.first()
        if not _staff:
            _staff = _cluster.staff.first()

        death_date = Utils.to_date_string(fake.date_this_month(before_today=True, after_today=False))
        preg_outcome_date = Utils.to_date_string(fake.date_this_month(before_today=True, after_today=False))
        props = {
            "__id": f"uuid:{uuid.uuid4()}",
            "__system": {
                "deviceId": f"collect:{uuid.uuid4()}",
                "formVersion": "1",
                "submissionDate": str(datetime.now()),
                "submitterId": _staff.id,
                "submitterName": fake.name(),
            },
            "grp_area": {
                "area_id": _area.code if _area else "AB123",
                "worker_id": _staff.code if _staff else "T123",
            },
            "grp_cluster": {
                "cluster_id": _cluster.code if _cluster else "1234AB",
            },
            "meta": {
                "instanceID": f"uuid:{uuid.uuid4()}",
                "instanceName": str(uuid.uuid4())
            },
            "death_date": death_date,
            "preg_outcome_date": preg_outcome_date,
            "dec_person_name": fake.name(),
            "mother_name": fake.name(),
            "today_date": death_date,
            "gps": {
                "coordinates": [-115, 36, 585],
                "properties": {
                    "accuracy": 30.123
                },
                "type": "Point"
            },
            "event_location": Event.EventLocationType.HOME.value,
            "event_type": Event.EventType.NO_EVENT.value,
            "visit_method": Event.VisitMethod.HOME_VISIT.value,
            "visit_type": Event.VisitType.ROUTINE_VISIT.value,
            "consent": Event.YesNo.YES.value,
            "consent_type": Event.ConsentType.GENERAL.value,
            "hh_address": fake.street_address(),
            "hh_head_name": fake.name(),
            "hh_id": "123",
            "resp_name": fake.name()
        }

        if for_death:
            death_props = {
                "grp_consent": {
                    "event_type": Event.EventType.DEATH.value,
                    "age_in_days": "2",
                    "dec_father_name": fake.name(),
                    "dec_mother_name": fake.name(),
                    "dob_date": Utils.to_date_string(fake.date_this_month(before_today=True, after_today=False)),
                    "dob_known": Event.YesNo.YES.value,
                    "is_neonatal": True
                }
            }
            props.update(death_props)
            death_props = cls.create_from_etl(for_death, **props)
            props.update(death_props)
        elif for_baby:
            baby_props = {
                "grp_consent": {
                    "event_type": Event.EventType.PREGNANCY.value,
                    "age_in_days": "2",
                    "dob_date": Utils.to_date_string(fake.date_this_month(before_today=True, after_today=False)),
                    "dob_known": Event.YesNo.YES.value,
                    "baby_ct": "1",
                    "baby_rep": []
                }
            }
            props.update(baby_props)
            baby_rep_props = {
                "__id": str(uuid.uuid4()),
                "baby_name": fake.name(),
                "baby_reg": "2",
                "baby_sex": fake.random_element(elements=[choice.value for choice in Baby.SexType]),
                "baby_wgt": 3500
            }
            baby_props = cls.create_from_etl(for_baby, **baby_rep_props)
            props['grp_consent']['baby_rep'].append(baby_props)

        props.update(kwargs)
        result = cls.create_from_etl(etl_document, **props)
        return result

    @classmethod
    def create_household(cls,
                         etl_document,
                         for_member=False,
                         _province=None, _cluster=None, _area=None, _staff=None, **kwargs):
        if not _province:
            _province = Province.objects.order_by("?").first()
            if not _province:
                _province = ProvinceFactory(with_clusters=True,
                                            with_clusters__with_areas=True,
                                            with_clusters__with_staff=True)
        if not _cluster:
            _cluster = _province.clusters.first()
        if not _area:
            _area = _cluster.areas.first()
        if not _staff:
            _staff = _cluster.staff.first()

        event_date = Utils.to_date_string(fake.date_this_month(before_today=True, after_today=False))
        props = {
            "__id": f"uuid:{uuid.uuid4()}",
            "__system": {
                "deviceId": f"collect:{uuid.uuid4()}",
                "formVersion": "1",
                "submissionDate": str(datetime.now()),
                "submitterId": _staff.id,
                "submitterName": fake.name(),
            },
            "grp_area": {
                "area_id": _area.code if _area else "AB123",
                "worker_id": _staff.code if _staff else "T123",
            },
            "grp_cluster": {
                "cluster_id": _cluster.code if _cluster else "1234AB",
            },
            "meta": {
                "instanceID": f"uuid:{uuid.uuid4()}",
                "instanceName": str(uuid.uuid4())
            },
            "event_date": event_date,
            "event_person_name": fake.name(),
            "today_date": event_date,
            "gps": {
                "coordinates": [-115, 36, 585],
                "properties": {
                    "accuracy": 30.123
                },
                "type": "Point"
            },
            "event_location": Event.EventLocationType.HOME.value,
            "event_type": Event.EventType.NO_EVENT.value,
            "visit_method": Event.VisitMethod.HOME_VISIT.value,
            "visit_type": Event.VisitType.ROUTINE_VISIT.value,
            "consent": Event.YesNo.YES.value,
            "consent_type": Event.ConsentType.GENERAL.value,
            "hh_address": fake.street_address(),
            "hh_head_name": fake.name(),
            "hh_id": "123",
            "resp_name": fake.name(),
            "grp_age": {
                "age_unit": "",
                "person_age": "1"
            },
            "grp_consent": {
                "consent": Household.ConsentType.YES.value,
                "grp_phone_cont": {
                    "any_phone": fake.phone_number(),
                    "any_phone_allow": Household.PhoneAllowType.YES.value,
                    "any_phone_conf": fake.phone_number(),
                    "any_phone_name": fake.name(),
                    "any_phone_poss": Household.YesNoType.YES.value,
                    "head_phone": fake.phone_number(),
                    "head_phone_allow": Household.PhoneAllowType.YES.value,
                    "head_phone_conf": fake.phone_number(),
                    "head_phone_poss": Household.YesNoType.YES.value,
                    "res_phone": fake.phone_number(),
                    "res_phone_allow": Household.PhoneAllowType.YES.value,
                    "res_phone_conf": fake.phone_number(),
                    "res_phone_poss": Household.ResPhonePossType.YES.value
                },
                "note_consent": ""
            }
        }

        if for_member:
            member_props = {
                "rep_member": []
            }
            props.update(member_props)
            member_rep_props = {
                "__id": str(uuid.uuid4()),
                "age_in_years": 39,
                "full_name": fake.name(),
                "mem_type": HouseholdMember.MemberType.RESIDENT.value,
                "rel_head": HouseholdMember.RelationHeadType.HEAD.value,
                "sex": fake.random_element(elements=[choice.value for choice in HouseholdMember.SexType]),
            }
            member_props = cls.create_from_etl(for_member, **member_rep_props)
            props['rep_member'].append(member_props)

        props.update(kwargs)
        result = cls.create_from_etl(etl_document, **props)
        return result

    @classmethod
    def create_verbal_autopsy(cls, etl_document, death, _province=None, _cluster=None, _area=None, _staff=None,
                              **kwargs):
        if not _province:
            _province = Province.objects.order_by("?").first()
            if not _province:
                _province = ProvinceFactory(with_clusters=True,
                                            with_clusters__with_areas=True,
                                            with_clusters__with_staff=True)
        if not _cluster:
            _cluster = _province.clusters.first()
            if not _cluster:
                _cluster = ClusterFactory(province=_province, with_areas=True)
        if not _area:
            _area = _cluster.areas.first()
            if not _area:
                _area = AreaFactory(cluster=_cluster)
        if not _staff:
            _staff = _cluster.staff.first()
            if not _staff:
                _staff = StaffFactory(cluster=_cluster)

        event_date = Utils.to_date_string(fake.date_this_month(before_today=True, after_today=False))
        props = {
            "__id": f"uuid:{uuid.uuid4()}",
            "__system": {
                "deviceId": f"collect:{uuid.uuid4()}",
                "formVersion": "1",
                "submissionDate": str(datetime.now()),
                "submitterId": _staff.id,
                "submitterName": fake.name(),
            },
            "meta": {
                "instanceID": f"uuid:{uuid.uuid4()}"
            },
            "cluster_id": _cluster.code if _cluster else "1234AB",
            "area_id": _area.code if _area else "AB123",
            "death_id": death.death_code,
            "respondent_backgr": {
                "Id10012": event_date,
            },
            "household_id": "123",
            "deceased_list": str(uuid.uuid4())
        }

        props.update(kwargs)
        result = cls.create_from_etl(etl_document, **props)
        return result

    @classmethod
    def create_from_etl(cls, etl_document, **kwargs):
        """
        Creates a FormSubmission dict from an ETL Document.

        Args:
            etl_document: The ETL Document to create the dict from.
            **kwargs: Key/Values to set. The key is the EtlMapping.source_name.

        Returns:
            Dict
        """
        result = {} if not kwargs else kwargs.copy()
        # Create all the objects to hold the properties.
        for etl_mapping in etl_document.etl_mappings.all():
            source_name_paths = etl_mapping.source_name.split('.')

            if len(source_name_paths) > 1:
                last_obj = result
                for prop in source_name_paths[:-1]:
                    if prop not in last_obj:
                        last_obj[prop] = {}
                    last_obj = last_obj[prop]

        # Set the properties.
        for etl_mapping in etl_document.etl_mappings.all():
            source_name_paths = etl_mapping.source_name.split('.')
            last_obj = result
            for prop in source_name_paths:
                if prop.endswith(']'):
                    prop = prop.rsplit('[', 1)[0]
                    if prop in kwargs:
                        last_obj[prop] = kwargs[prop]
                    elif prop not in last_obj:
                        last_obj[prop] = []
                    break

                if prop not in last_obj:
                    if etl_mapping.default is not None:
                        last_obj[prop] = etl_mapping.default
                    else:
                        if etl_mapping.target_type == TypeCaster.TypeCode.INT:
                            last_obj[prop] = 0
                        elif etl_mapping.target_type == TypeCaster.TypeCode.FLOAT:
                            last_obj[prop] = 0.0
                        elif etl_mapping.target_type == TypeCaster.TypeCode.STR:
                            last_obj[prop] = ''
                        elif etl_mapping.target_type == TypeCaster.TypeCode.BOOL:
                            last_obj[prop] = False
                        elif etl_mapping.target_type == TypeCaster.TypeCode.DICT:
                            last_obj[prop] = {}
                        elif etl_mapping.target_type == TypeCaster.TypeCode.LIST:
                            last_obj[prop] = []
                        elif etl_mapping.target_type == TypeCaster.TypeCode.DATE:
                            last_obj[prop] = Utils.to_date_string(
                                fake.date_this_month(before_today=True, after_today=False))
                        elif etl_mapping.target_type == TypeCaster.TypeCode.DATETIME:
                            last_obj[prop] = Utils.to_datetime_string(
                                fake.date_time_this_month(before_now=True, after_now=False))
                        else:
                            last_obj[prop] = {}
                last_obj = last_obj[prop]

        return result
