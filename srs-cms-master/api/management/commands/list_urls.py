from django.core.management.base import BaseCommand
from django.urls import get_resolver, URLPattern, URLResolver


def list_urls(urlpatterns, prefix=""):
    url_list = []

    for pattern in urlpatterns:
        if isinstance(pattern, URLPattern):
            callback = pattern.callback
            if hasattr(callback, '__name__'):
                name = callback.__name__
            elif hasattr(callback, '__class__'):
                name = callback.__class__.__name__
            else:
                name = str(callback)
            url_list.append({
                'pattern': f"{prefix}{pattern.pattern}",
                'name': pattern.name,
                'callback': name,
            })

        elif isinstance(pattern, URLResolver):
            nested = list_urls(pattern.url_patterns, prefix=f"{prefix}{pattern.pattern}/")
            url_list.extend(nested)

    return url_list


class Command(BaseCommand):
    help = 'List all registered URLs in the project, including Admin URLs.'

    def handle(self, *args, **kwargs):
        resolver = get_resolver()
        urls = list_urls(resolver.url_patterns)

        for url in urls:
            self.stdout.write(f"{url['pattern']:80} | view: {url['callback']} | name: {url['name']}")
