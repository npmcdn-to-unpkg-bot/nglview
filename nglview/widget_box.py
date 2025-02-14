from __future__ import absolute_import
from ipywidgets import Box, DOMWidget
from .widget import NGLWidget
from .layout import form_item_layout
from . import default
from .utils import js_utils
from traitlets import CaselessStrEnum, observe, Unicode

class BoxNGL(Box):
    _gui_style = CaselessStrEnum(['row', 'column'], default_value='row').tag(sync=True)

    def __init__(self, *args, **kwargs):
        super(BoxNGL, self).__init__(*args, **kwargs)

        self.layout = form_item_layout

    @observe('_gui_style')
    def _update_gui_style(self, change):
        """row or column style
        """
        what = change['new']
        self.layout.flex_flow = what.lower()

    def _ipython_display_(self, *args, **kwargs):
        for widget in self.children:
            if isinstance(widget, NGLWidget):
                widget.displayed = True
        super(BoxNGL, self)._ipython_display_(*args, **kwargs)

    def _update_size(self):
        for widget in self.children:
            if isinstance(widget, NGLWidget):
                  widget._remote_call('setSize', target='Widget', args=['50%', '50%'])

    def _beautify(self):
        js_utils._set_notebook_width('60%', left_padding=None)
        self._update_size()

class DraggableBox(Box):
    _view_name = Unicode("NGLBox").tag(sync=True)
    _view_module = Unicode("nglview-js").tag(sync=True)
    _dialog = Unicode('off').tag(sync=True)
