import importlib


class EntityListExporterFactory:
    ODK_VA_PRELOAD_EXPORTER_NAME = 'VAPreloadExporter'
    ODK_VA_PRELOAD_EXPORTER_CLASS = 'api.odk.exporters.entity_lists.va_preload_exporter.VaPreloadExporter'

    ODK_EXPORTERS = [
        (ODK_VA_PRELOAD_EXPORTER_CLASS, ODK_VA_PRELOAD_EXPORTER_NAME),
    ]

    # Choices for the Models. This returns a tuple of (name, name).
    ODK_EXPORTERS_CHOICES = list(map(lambda i: (i[1], i[1]), ODK_EXPORTERS))

    _MODULE_MAP = {}

    @classmethod
    def get_exporter(cls, exporter_class, *args, **kwargs):
        if hasattr(exporter_class, 'exporter'):
            exporter_class = getattr(exporter_class, 'exporter')
        klass = cls.get_exporter_class(exporter_class)
        if not klass:
            print('Exporter not found: {}'.format(exporter_class))
        else:
            if klass not in cls._MODULE_MAP:
                module_name = '.'.join(klass.split('.')[:-1])
                class_name = klass.split('.')[-1]
                cls._MODULE_MAP[klass] = (module_name, class_name)
            else:
                module_name, class_name = cls._MODULE_MAP[klass]

            module = importlib.import_module(module_name)
            class_ = getattr(module, class_name)
            exporter = class_(*args, **kwargs)
            return exporter

    @classmethod
    def get_exporter_class(cls, exporter_class):
        for klass, name in cls.ODK_EXPORTERS:
            if klass == exporter_class or name == exporter_class:
                return klass

    @classmethod
    def get_exporter_class_name(cls, exporter_class):
        for klass, name in cls.ODK_EXPORTERS:
            if klass == exporter_class or name == exporter_class:
                return name
