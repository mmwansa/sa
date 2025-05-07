import json
from api.odk.transformers.transformer_factory import TransformerFactory


class TransformField:
    """
    Concrete class for EtlMapping.transform JSON.
    """

    def __init__(self, name=None, args=[], kwargs=[]):
        self.name = name
        self.args = args
        self.kwargs = kwargs

    @classmethod
    def get(cls, transform):
        if isinstance(transform, cls):
            return transform
        elif isinstance(transform, str):
            transform = json.loads(transform)
        return cls(**transform)

    def transform(self, value):
        transformer = TransformerFactory.get_transformer(self.name)
        return transformer.transform(value, self)
