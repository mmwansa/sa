from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def transform_query(context, **kwargs):
    """Modify URL query parameters while keeping existing params."""
    query = context['request'].GET.copy()
    for k, v in kwargs.items():
        query[k] = v
    return query.urlencode()
