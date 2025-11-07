from netbox.plugins import PluginMenuItem
from netbox.navigation import create_menu_items

menu_items = (
    PluginMenuItem(
        link='plugins:device_map:map',
        link_text='Device Map',
        permissions=('dcim.view_device',),
    ),
)

create_menu_items('plugins', menu_items)
