import importlib


class TransformerFactory:
    REPLACE_TRANSFORMER = 'api.odk.transformers.replace_transformer.ReplaceTransformer'
    REPLACE_TRANSFORMER_NAME = 'replace'

    STRFTIME_TRANSFORMER = 'api.odk.transformers.strftime_transformer.StrftimeTransformer'
    STRFTIME_TRANSFORMER_NAME = 'strftime'

    TRANSFORMERS = [
        (REPLACE_TRANSFORMER, REPLACE_TRANSFORMER_NAME),
        (STRFTIME_TRANSFORMER, STRFTIME_TRANSFORMER_NAME),
    ]

    @classmethod
    def get_transformer(cls, transformer_name, *args, **kwargs):
        klass, _name = next((t for t in cls.TRANSFORMERS if t[1] == transformer_name), None)
        if not klass:
            raise Exception('Transformer not found: {}'.format(transformer_name))
        else:
            module_name = '.'.join(klass.split('.')[:-1])
            class_name = klass.split('.')[-1]
            module = importlib.import_module(module_name)
            class_ = getattr(module, class_name)
            transformer = class_(*args, **kwargs)
            return transformer

    @classmethod
    def _get_transformer_class(cls, transformer_class):
        klass = next((i[0] for i in cls.TRANSFORMERS if i[0] == transformer_class), None)
        return klass
