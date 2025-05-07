class QueryExtensionMixin:
    @classmethod
    def find_by(cls, **kwargs):
        return cls.objects.filter(**kwargs).first()

    @classmethod
    def filter_by(cls, **kwargs):
        return cls.objects.filter(**kwargs)
