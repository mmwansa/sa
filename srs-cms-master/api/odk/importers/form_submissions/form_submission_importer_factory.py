import importlib


class FromSubmissionImporterFactory:
    ODK_EVENTS_IMPORTER_NAME = 'EventsImporter'
    ODK_EVENTS_IMPORTER_CLASS = 'api.odk.importers.form_submissions.events_importer.EventsImporter'

    ODK_DEATHS_IMPORTER_NAME = 'DeathsImporter'
    ODK_DEATHS_IMPORTER_CLASS = 'api.odk.importers.form_submissions.deaths_importer.DeathsImporter'

    ODK_BABIES_IMPORTER_NAME = 'BabiesImporter'
    ODK_BABIES_IMPORTER_CLASS = 'api.odk.importers.form_submissions.babies_importer.BabiesImporter'

    ODK_HOUSEHOLDS_IMPORTER_NAME = 'HouseholdsImporter'
    ODK_HOUSEHOLDS_IMPORTER_CLASS = 'api.odk.importers.form_submissions.households_importer.HouseholdsImporter'

    ODK_HOUSEHOLD_MEMBERS_IMPORTER_NAME = 'HouseholdMembersImporter'
    ODK_HOUSEHOLD_MEMBERS_IMPORTER_CLASS = 'api.odk.importers.form_submissions.household_members_importer.HouseholdMembersImporter'

    ODK_VERBALAUTOPSY_IMPORTER_NAME = 'VerbalAutopsiesImporter'
    ODK_VERBALAUTOPSY_IMPORTER_CLASS = 'api.odk.importers.form_submissions.verbal_autopsies_importer.VerbalAutopsiesImporter'

    ODK_EVENT_IMPORTERS = [
        (ODK_EVENTS_IMPORTER_CLASS, ODK_EVENTS_IMPORTER_NAME),
        (ODK_DEATHS_IMPORTER_CLASS, ODK_DEATHS_IMPORTER_NAME),
        (ODK_BABIES_IMPORTER_CLASS, ODK_BABIES_IMPORTER_NAME),
    ]

    ODK_HOUSEHOLD_IMPORTERS = [
        (ODK_HOUSEHOLDS_IMPORTER_CLASS, ODK_HOUSEHOLDS_IMPORTER_NAME),
        (ODK_HOUSEHOLD_MEMBERS_IMPORTER_CLASS, ODK_HOUSEHOLD_MEMBERS_IMPORTER_NAME),
    ]

    ODK_VERBAL_AUTOPSY_IMPORTERS = [
        (ODK_VERBALAUTOPSY_IMPORTER_CLASS, ODK_VERBALAUTOPSY_IMPORTER_NAME)
    ]

    ODK_IMPORTERS = ODK_EVENT_IMPORTERS + ODK_HOUSEHOLD_IMPORTERS + ODK_VERBAL_AUTOPSY_IMPORTERS

    # Choices for the Models. This returns a tuple of (name, name).
    ODK_IMPORTERS_CHOICES = list(map(lambda i: (i[1], i[1]), ODK_IMPORTERS))

    _MODULE_MAP = {}

    @classmethod
    def get_importer(cls, importer_class, *args, **kwargs):
        if hasattr(importer_class, 'importer'):
            importer_class = getattr(importer_class, 'importer')
        klass = cls.get_importer_class(importer_class)
        if not klass:
            print('Importer not found: {}'.format(importer_class))
        else:
            if klass not in cls._MODULE_MAP:
                module_name = '.'.join(klass.split('.')[:-1])
                class_name = klass.split('.')[-1]
                cls._MODULE_MAP[klass] = (module_name, class_name)
            else:
                module_name, class_name = cls._MODULE_MAP[klass]

            module = importlib.import_module(module_name)
            class_ = getattr(module, class_name)
            importer = class_(*args, **kwargs)
            return importer

    @classmethod
    def get_importer_class(cls, importer_class):
        for klass, name in cls.ODK_IMPORTERS:
            if klass == importer_class or name == importer_class:
                return klass

    @classmethod
    def get_importer_class_name(cls, importer_class):
        for klass, name in cls.ODK_IMPORTERS:
            if klass == importer_class or name == importer_class:
                return name
