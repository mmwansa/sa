class ReplaceTransformer:
    def transform(self, value, transform_field):
        if value is None:
            return value
        if not isinstance(value, str):
            value = str(value)
        return value.replace(*transform_field.args or [], **transform_field.kwargs or {})
