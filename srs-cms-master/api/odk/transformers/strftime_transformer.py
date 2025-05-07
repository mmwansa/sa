class StrftimeTransformer:
    def transform(self, value, transform_field):
     #   if value is None:
        if value is None or value == '':
            return value
        return value.strftime(*transform_field.args or [], **transform_field.kwargs or {})
