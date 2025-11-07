import logging
import re
from dcim.models import Device, Interface
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from . import forms
from .geographical_map import configure_leaflet_map
from .helpers import get_device_location, get_connected_devices
from .settings import plugin_settings

logger = logging.getLogger(__name__)
INTEGER_REGEXP = re.compile(r'\d+')

class MapView(PermissionRequiredMixin, View):
    permission_required = ('ipam.view_vlan', 'dcim.view_device', 'dcim.view_devicerole', 'dcim.view_cable')
    template_name = 'netbox_device_map/main.html'
    form = forms.DeviceMapFilterForm

    def get(self, request):
        """Device map view"""
        form = self.form(request.GET)
        if form.is_valid():
            interfaces = Interface.objects.all()
            vlan = form.cleaned_data['vlan']
            if vlan:  # Guard: Only filter if VLAN selected
                interfaces = interfaces.filter(Q(untagged_vlan=vlan) | Q(tagged_vlans=vlan))
            devices = Device.objects.filter(interfaces__in=interfaces).distinct().prefetch_related(
                'custom_field_values__custom_field',  # FIXED: Proper prefetch for custom fields (avoids N+1)
                'device_role',  # For role checks
            )
            if device_roles := form.cleaned_data['device_roles']:
                devices = devices.filter(device_role__in=device_roles)
            geolocated_devices = {d: coords for d in devices if (coords := get_device_location(d))}
            non_geolocated_devices = set(devices) - set(geolocated_devices.keys())
            map_data = configure_leaflet_map(
                "geomap", geolocated_devices, form.cleaned_data['calculate_connections']
            )
            map_data['vlan'] = vlan.id if vlan else None  # VLAN guard (prevents None.id crash)
            return render(request, self.template_name, context=dict(
                filter_form=form, map_data=map_data, non_geolocated_devices=non_geolocated_devices
            ))
        logger.warning(f"Invalid form data in MapView: {form.errors}")
        return render(
            request, self.template_name,
            context=dict(filter_form=self.form(initial=request.GET))
        )

class ConnectedCpeAjaxView(PermissionRequiredMixin, View):
    permission_required = ('dcim.view_device', 'dcim.view_cable')
    form = forms.ConnectedCpeForm

    def get(self, request, **kwargs):
        """List of CPE devices connected to the specified node device"""
        try:
            device = Device.objects.get(pk=kwargs.get('pk'))
        except Device.DoesNotExist:
            return JsonResponse({'status': False, 'error': 'Device not found'}, status=404)
        form = self.form(request.GET)
        if form.is_valid():
            data = form.cleaned_data
            connected_devices_qs = get_connected_devices(device, vlan=data['vlan'])\
                .filter(device_role__name=plugin_settings['cpe_device_role']).order_by()
            connected_devices = [
                dict(
                    id=d.id,
                    name=d.name,
                    url=d.get_absolute_url(),
                    comments=getattr(d, 'comments', '')  # Guard empty/None comments
                )
                for d in connected_devices_qs
            ]
            # Sorting list of CPE devices by the sequence of integers contained in the comments
            connected_devices.sort(key=lambda d: tuple(int(n) for n in INTEGER_REGEXP.findall(d['comments'] or '')))
            # Guard for missing device_type/manufacturer
            manuf = getattr(device.device_type.manufacturer, 'name', 'Unknown') if device.device_type else 'Unknown'
            model = getattr(device.device_type, 'model', 'Unknown') if device.device_type else 'Unknown'
            device_type = f"{manuf} {model}"
            return JsonResponse(dict(
                status=True,
                cpe_devices=connected_devices,
                device_type=device_type
            ))
        else:
            return JsonResponse({
                'status': False,
                'error': 'Form fields filled out incorrectly',
                'form_errors': form.errors
            }, status=400)  # Better: 400 for invalid input
