from django.conf import settings
from . import config

user_config = settings.PLUGINS_CONFIG.get(config.name, {})
plugin_settings = config.default_settings | user_config
plugin_settings['geomap_settings'] = (
    config.default_settings['geomap_settings'] | 
    plugin_settings.get('geomap_settings', {})
)
