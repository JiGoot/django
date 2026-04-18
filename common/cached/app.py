from typing import TYPE_CHECKING, Optional
from datetime import date, timedelta
import logging
from django.core.cache import cache
from core.utils import ReleaseStages, formattedError
from django.db.models.query import QuerySet
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from common.models.app import App, Release


class CachedApp:

    class Key:
        def __init__(self, app: 'App'):
            base = f'app|{app.id}'
            self.releases = f'{base}|releases'

    def __init__(self, app: 'App') -> None:
        self.app = app
        self.keys = self.Key(app)

    @property
    def releases(self) -> QuerySet['Release']:
        '''Retrieve affiches for the city or query and cache them'''

        """Return the latest version for the given app."""
        key = self.keys.releases
        try:
            cached = cache.get(key)
            return cached
        except Exception as e:
            cache.delete(key)
        releases = self.app.releases.order_by("-created_at")
        cache.set(key, releases, timedelta(hours=1).total_seconds())
        return releases
    
    @property
    def last_release(self) -> Optional['Release']:
        '''Get the latest release for the app, if available.'''
        return self.releases.first()


# def clear_last_version(sender, instance: 'Release', **kwargs):
#     try:
#         app = instance.app
#         cache.delete(app.cached.keys.last_release)
#     except Exception as e:
#         logger.error(formattedError(e))

# Connect manually using function name dynamically
# from django.db.models.signals import post_save, post_delete
# for signal in [post_save, post_delete]:
#     signal.connect(clear_last_version, sender='Release', dispatch_uid=f"{__name__}.{clear_last_version.__name__}")