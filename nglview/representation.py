from __future__ import absolute_import
from traitlets import Int, Dict, Any, observe, Bool
from ipywidgets import Box, DOMWidget, interactive
from ipywidgets import VBox

# local
from .color import COLOR_SCHEMES
from .utils import widget_utils, py_utils
from .layout import _relayout_master

class RepresentationControl(Box):
    parameters = Dict().tag(sync=False)
    name = Any().tag(sync=False)
    repr_index = Int().tag(sync=False)
    component_index = Int().tag(sync=False)
    _disable_update_parameters = Bool(False).tag(sync=False)

    def __init__(self, view, component_index, repr_index, name=None, *args, **kwargs):
        super(RepresentationControl, self).__init__(*args, **kwargs)
        self.component_index = component_index   
        self.repr_index = repr_index
        self._view = view
        self.children = self._make_widget().children
        # trigger
        self.name = name

    def _on_change_widget_value(self, change):
        owner = change['owner']
        new = change['new']
        self.parameters = {py_utils._camelize(owner._ngl_description): new}

    @observe('parameters')
    def _on_parameters_changed(self, change):
        if not self._disable_update_parameters:
            parameters = change['new']

            self._view.update_representation(component=self.component_index,
                    repr_index=self.repr_index,
                    **parameters)

    @observe('name')
    def _on_name_changed(self, change):
        new_name = change['new']
        if new_name == 'surface':
            for kid in self.children:
                if kid._ngl_type == 'surface':
                    kid.layout.display = 'flex'
        else:
            for kid in self.children:
                if kid._ngl_type == 'surface':
                    kid.layout.display = 'none'

    def _get_name_and_repr_dict(self, c_string, r_string):
        try:
            _repr_dict = self._view._repr_dict[c_string][r_string]['parameters']
            name = self._view._repr_dict[c_string][r_string]['name']
        except KeyError:
            _repr_dict = dict()
            name = ''

        return name, _repr_dict

    @observe('repr_index')
    def _on_repr_index_changed(self, change):
        c_string = 'c' + str(self.component_index)
        r_string = str(change['new'])
        name, _repr_dict = self._get_name_and_repr_dict(c_string, r_string)
        self.name = name
        self._disable_update_parameters = True
        for kid in self.children:
            desc = py_utils._camelize(kid._ngl_description)
            if desc in _repr_dict:
                kid.value = _repr_dict.get(desc)
        self._disable_update_parameters = False

    def _make_widget(self):
        c_string = 'c' + str(self.component_index)
        r_string = str(self.repr_index)
        name, _repr_dict = self._get_name_and_repr_dict(c_string, r_string)

        assembly_list = ['default', 'AU', 'BU1', 'UNITCELL', 'SUPERCELL']
        surface_types = ['vws', 'sas', 'ms', 'ses']

        def func(opacity=_repr_dict.get('opacity', 1.),
                 assembly=_repr_dict.get('assembly', 'default'),
                 color_scheme=_repr_dict.get('colorScheme', " "),
                 wireframe=_repr_dict.get('wireframe', False),
                 probe_radius=_repr_dict.get('probeRadius', 1.4),
                 isolevel=_repr_dict.get('isolevel', 2.),
                 smooth=_repr_dict.get('smooth', 2.),
                 surface_type=_repr_dict.get('surfaceType', 'ms'),
                 box_size=_repr_dict.get('boxSize', 10),
                 cutoff=_repr_dict.get('cutoff', 0)):
            pass

        widget = interactive(func, opacity=(0., 1., 0.1),
                                 color_scheme=COLOR_SCHEMES,
                                 assembly=assembly_list,
                                 probe_radius=(0., 5., 0.1),
                                 isolevel=(0., 10., 0.1),
                                 smooth=(0, 10, 1),
                                 surface_type=surface_types,
                                 box_size=(0, 100, 2),
                                 cutoff=(0., 100, 0.1),
                                 continuous_update=False)
        for kid in widget.children:
            setattr(kid, '_ngl_description', kid.description)
            if kid._ngl_description in ['probe_radius', 'smooth', 'surface_type', 'box_size', 'cutoff']:
                setattr(kid, '_ngl_type', 'surface')
            else:
                setattr(kid, '_ngl_type', 'basic')
            kid.observe(self._on_change_widget_value, 'value')
        return widget
