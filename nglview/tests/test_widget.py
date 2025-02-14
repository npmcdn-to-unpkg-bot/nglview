# adpated from Jupyter ipywidgets project.

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function
import os

import nose.tools as nt
import gzip
import unittest
import pytest
from numpy.testing import assert_equal as eq, assert_almost_equal as aa_eq
import numpy as np

from ipykernel.comm import Comm
import ipywidgets
from ipywidgets import Widget, IntText, BoundedFloatText, HBox
from traitlets import TraitError
import ipywidgets as widgets
from traitlets import TraitError, link
from IPython import display

import pytraj as pt
import nglview as nv
from nglview import NGLWidget
from nglview import widget_utils
import mdtraj as md
import parmed as pmd
from nglview.utils.py_utils import PY2, PY3
from nglview import js_utils
from nglview.representation import RepresentationControl
from nglview.utils.py_utils import encode_base64, decode_base64
from nglview import interpolate

# local
from utils import get_fn, repr_dict as REPR_DICT

def default_view():
    traj = pt.load(nv.datafiles.TRR, nv.datafiles.PDB)
    return nv.show_pytraj(traj)

#-----------------------------------------------------------------------------
# Utility stuff from ipywidgets tests
#-----------------------------------------------------------------------------

class DummyComm(Comm):
    comm_id = 'a-b-c-d'

    def open(self, *args, **kwargs):
        pass

    def send(self, *args, **kwargs):
        pass

    def close(self, *args, **kwargs):
        pass

_widget_attrs = {}
displayed = []
undefined = object()

def setup():
    _widget_attrs['_comm_default'] = getattr(Widget, '_comm_default', undefined)
    Widget._comm_default = lambda self: DummyComm()
    _widget_attrs['_ipython_display_'] = Widget._ipython_display_
    def raise_not_implemented(*args, **kwargs):
        raise NotImplementedError()
    Widget._ipython_display_ = raise_not_implemented


def teardown():
    for attr, value in _widget_attrs.items():
        if value is undefined:
            delattr(Widget, attr)
        else:
            setattr(Widget, attr, value)

#-----------------------------------------------------------------------------
# NGLView stuff
#-----------------------------------------------------------------------------

DEFAULT_REPR = [{'params': {'sele': 'polymer'}, 'type': 'cartoon'},
                {'params': {'sele': 'hetero OR mol'}, 'type': 'ball+stick'},
                {"type": "ball+stick", "params": {"sele": "not protein and not nucleic"}}
                ]

def _assert_dict_list_equal(listdict0, listdict1):
    for (dict0, dict1) in zip(listdict0, listdict1):
        for (key0, key1) in zip(sorted(dict0.keys()), sorted(dict1.keys())):
            nt.assert_equal(key0, key1)
            nt.assert_equal(dict0.get(key0), dict1.get(key1))

def test_API_promise_to_have():
    view = nv.demo()

    # Structure
    structure = nv.Structure()
    structure.get_structure_string
    nt.assert_true(hasattr(structure, 'id'))
    nt.assert_true(hasattr(structure, 'ext'))
    nt.assert_true(hasattr(structure, 'params'))

    # Widget
    nv.NGLWidget._set_coordinates
    nv.NGLWidget._set_initial_structure

    nv.NGLWidget.add_component
    nv.NGLWidget.add_trajectory
    nv.NGLWidget.coordinates_dict
    nv.NGLWidget.set_representations
    nv.NGLWidget.clear
    nv.NGLWidget.center

    # add component
    view.add_component('rcsb://1tsu.pdb')
    view.add_pdbid('1tsu')

    # display
    js_utils.clean_error_output()
    display.display(view.player.widget_repr)
    view.player._display()

    # show
    nv.show_pdbid('1tsu')
    nv.show_url('https://dummy.pdb')
    # other backends will be tested in other sections

    # constructor
    ngl_traj = nv.PyTrajTrajectory(pt.datafiles.load_ala3())
    nv.NGLWidget(ngl_traj, parameters=dict(background_color='black'))
    nv.NGLWidget(ngl_traj, representations=[dict(type='cartoon')])

    view.parameters
    view.camera
    view.camera = 'perspective'
    view._request_stage_parameters()
    view._repr_dict = REPR_DICT

    # dummy
    class DummWidget():
        value = ''

    view.player.picked_widget = DummWidget()

    view._update_background_color(change=dict(new='blue'))
    view.on_update_dragged_file(change=dict(new=2, old=1))
    view.on_update_dragged_file(change=dict(new=1, old=1))
    tab = view.player._display()

    view.player.widget_repr = view.player._make_widget_repr()
    view._handle_n_components_changed(change=dict(new=2, old=1))
    view._handle_n_components_changed(change=dict(new=1, old=1))
    view.on_loaded(change=dict(new=True))
    view.on_loaded(change=dict(new=False))
    view._refresh_render()
    view.sync_view()

    def _dummy():
        pass
    view._ipython_display_ = _dummy
    view._ipython_display_()

    view.display(gui=True)
    view.display(gui=False)
    view._set_draggable(True)
    view._set_draggable(False)
    view._set_sync_frame()
    view._set_sync_camera()
    view._set_spin([0, 1, 0], 0.5)
    view._set_selection('.CA')
    view.color_by('atomindex')
    representations = [dict(type='cartoon', params=dict())]
    view.representations = representations
    repr_parameters = dict(opacity=0.3, params=dict())
    view.update_representation(parameters=repr_parameters)
    view._remove_representation()
    view.clear()
    view.add_representation('surface', selection='*', useWorker=True)
    view.add_representation('surface', selection='*', component=1)
    view.center()
    view._hold_image = True
    view._on_render_image(change=dict(new=u'xyz'))
    view._hold_image = False
    view._on_render_image(change=dict(new=u'xyz'))
    view.render_image()
    view.download_image()

    msg = dict(type='request_frame', data=dict())
    view._ngl_handle_msg(view, msg=msg, buffers=[])
    msg = dict(type='repr_parameters', data=dict(name='hello'))
    view._ngl_handle_msg(view, msg=msg, buffers=[])
    msg = dict(type='request_loaded', data=True)
    view._ngl_handle_msg(view, msg=msg, buffers=[])
    msg = dict(type='all_reprs_info', data=REPR_DICT)
    view._ngl_handle_msg(view, msg=msg, buffers=[])
    msg = dict(type='stage_parameters', data=dict())
    view._ngl_handle_msg(view, msg=msg, buffers=[])

    view.loaded = True
    view.show_only([0,])
    view._js_console()
    view._get_full_params()
    view.detach(split=False)
    view.detach(split=True)

def test_base_adaptor():
    # abstract base class
    def func_0():
        nv.Structure().get_structure_string()

    def func_1():
        nv.Trajectory().get_coordinates(1)
        nv.Trajectory().n_frames

    pytest.raises(NotImplementedError, func_0)
    pytest.raises(NotImplementedError, func_1)

def test_coordinates_dict():
    traj = pt.load(nv.datafiles.TRR, nv.datafiles.PDB)
    view = nv.show_pytraj(traj)
    view.frame = 1
    coords = view.coordinates_dict[0]
    aa_eq(coords, traj[1].xyz)

    # dummy
    view._send_binary = False
    view.coordinates_dict = {0: coords}

def test_load_data():
    view = nv.show_pytraj(pt.datafiles.load_tz2())

    # load blob with ext
    blob = open(nv.datafiles.PDB).read()
    view._load_data(blob, ext='pdb')

    # raise if passing blob but does not provide ext
    nt.assert_raises(ValueError, view._load_data, blob)

    # load PyTrajectory
    t0 = nv.PyTrajTrajectory(pt.datafiles.load_ala3())
    view._load_data(t0)

    # load current folder
    view._load_data(get_fn('tz2.pdb'))

def test_representations():
    view = nv.show_pytraj(pt.datafiles.load_tz2())
    nt.assert_equal(view.representations, DEFAULT_REPR)
    view.add_cartoon()
    representations_2 = DEFAULT_REPR[:]
    representations_2.append({'type': 'cartoon', 'params': {'sele': 'all'}})
    print(representations_2)
    print(view.representations)
    _assert_dict_list_equal(view.representations, representations_2)

    # Representations
    # make fake params
    try:
        view._repr_dict = {'c0': {'0': {'parameters': {}}}}
    except (KeyError, TraitError):
        # in real application, we are not allowed to assign values
        pass

    view._repr_dict = REPR_DICT
    representation_widget = RepresentationControl(view, 0, 0)
    representation_widget
    representation_widget._on_parameters_changed(change=dict(new=dict()))

def test_representation_control():
    view = nv.demo()
    repr_control = view._display_repr()
                    
def test_add_repr_shortcut():
    view = nv.show_pytraj(pt.datafiles.load_tz2())
    assert isinstance(view, nv.NGLWidget), 'must be instance of NGLWidget'

    # add
    view.add_cartoon(color='residueindex')
    view.add_rope(color='red')

    # update
    view.update_cartoon(opacity=0.4)
    view.update_rope(coor='blue')

    # remove
    view.remove_cartoon()
    view.remove_rope()

def test_add_new_shape():
    view = nv.NGLWidget()
    sphere = ('sphere', [0, 0, 9], [1, 0, 0], 1.5)
    arrow = ('arrow', [1, 2, 7 ], [30, 3, 3], [1, 0, 1], 1.0)
    view._add_shape([sphere, arrow], name='my_shape')

    # Shape
    view.shape.add_arrow([1, 2, 7 ], [30, 3, 3], [1, 0, 1], 1.0)

def test_remote_call():
    # how to test JS?
    view = nv.show_pytraj(pt.datafiles.load_tz2())
    view._remote_call('centerView', target='stage')

    fn = 'notebooks/tz2.pdb'
    kwargs = {'defaultRepresentation': True}
    view._remote_call('loadFile', target='stage', args=[fn,], kwargs=kwargs)

def test_download_image():
    """just make sure it can be called
    """
    view = nv.show_pytraj(pt.datafiles.load_tz2())
    view.download_image('myname.png', 2, False, False, True)

def test_show_structure_file():
    view = nv.show_structure_file(nv.datafiles.PDB)

def test_show_text():
    text = open(nv.datafiles.PDB).read()
    nv.show_text(text)

def test_show_simpletraj():
    traj = nv.SimpletrajTrajectory(nv.datafiles.XTC, nv.datafiles.GRO)
    view = nv.show_simpletraj(traj)
    view
    view.frame = 3

def test_show_mdtraj():
    import mdtraj as md
    from mdtraj.testing import get_fn
    fn = nv.datafiles.PDB 
    traj = md.load(fn)
    view = nv.show_mdtraj(traj)

def test_show_MDAnalysis():
    from MDAnalysis import Universe
    tn, fn = nv.datafiles.PDB, nv.datafiles.PDB
    u = Universe(fn, tn)
    view = nv.show_mdanalysis(u)

def test_show_parmed():
    import parmed as pmd
    fn = nv.datafiles.PDB 
    parm = pmd.load_file(fn)
    view = nv.show_parmed(parm)

    ngl_traj = nv.ParmEdTrajectory(parm)
    ngl_traj.only_save_1st_model = False
    ngl_traj.get_structure_string()

def test_encode_and_decode():
    xyz = np.arange(100).astype('f4')
    shape = xyz.shape

    b64_str = encode_base64(xyz)
    new_xyz = decode_base64(b64_str, dtype='f4', shape=shape)
    aa_eq(xyz, new_xyz) 

def test_coordinates_meta():
    from mdtraj.testing import get_fn
    fn, tn = [get_fn('frame0.pdb'),] * 2
    trajs = [pt.load(fn, tn), md.load(fn, top=tn), pmd.load_file(tn, fn)]

    N_FRAMES = trajs[0].n_frames

    from MDAnalysis import Universe
    u = Universe(tn, fn)
    trajs.append(Universe(tn, fn))

    views = [nv.show_pytraj(trajs[0]), nv.show_mdtraj(trajs[1]), nv.show_parmed(trajs[2])]
    views.append(nv.show_mdanalysis(trajs[3]))

    for index, (view, traj) in enumerate(zip(views, trajs)):
        view.frame = 3
        
        nt.assert_equal(view._trajlist[0].n_frames, N_FRAMES)

def test_structure_file():
    for fn in [get_fn('tz2.pdb'), nv.datafiles.GRO]:
        content = open(fn, 'rb').read()
        fs1 = nv.FileStructure(fn)
        nt.assert_equal(content, fs1.get_structure_string()) 
    
    # gz
    fn = get_fn('tz2_2.pdb.gz')
    fs2 = nv.FileStructure(fn)
    content = gzip.open(fn).read()
    nt.assert_equal(content, fs2.get_structure_string()) 

def test_camelize_parameters():
    view = nv.NGLWidget()
    view.parameters = dict(background_color='black')
    nt.assert_true('backgroundColor' in view._parameters) 

def test_component_for_duck_typing():
    view = NGLWidget()
    traj = pt.load(nv.datafiles.PDB)
    view.add_component(get_fn('tz2.pdb'))
    view.add_component(get_fn('tz2_2.pdb.gz'))
    view.add_trajectory(nv.PyTrajTrajectory(traj))
    view.component_0.add_representation('cartoon')
    
    c0 = view[0]
    c1 = view[1]
    nt.assert_true(hasattr(view, 'component_0'))
    nt.assert_true(hasattr(view, 'component_1'))
    nt.assert_true(hasattr(view, 'trajectory_0'))
    nt.assert_true(hasattr(view.trajectory_0, 'n_frames'))
    nt.assert_true(hasattr(view.trajectory_0, 'get_coordinates'))
    nt.assert_true(hasattr(view.trajectory_0, 'get_structure_string'))

    c0.show()
    c0.hide()

    view.remove_component(c0.id)
    nt.assert_false(hasattr(view, 'component_2'))

def test_trajectory_show_hide_sending_cooridnates():
    view = NGLWidget()

    traj0 = pt.datafiles.load_tz2()
    traj1 = pt.datafiles.load_trpcage()

    view.add_trajectory(nv.PyTrajTrajectory(traj0))
    view.add_trajectory(nv.PyTrajTrajectory(traj1))

    for traj in view._trajlist:
        nt.assert_true(traj.shown)

    view.frame = 1

    def copy_coordinate_dict(view):
        # make copy to avoid memory free
        return dict((k, v.copy()) for k, v in view.coordinates_dict.items())

    coordinates_dict = copy_coordinate_dict(view)
    aa_eq(coordinates_dict[0], traj0[1].xyz) 
    aa_eq(coordinates_dict[1], traj1[1].xyz) 

    # hide 0
    view.hide([0,])
    nt.assert_false(view._trajlist[0].shown)
    nt.assert_true(view._trajlist[1].shown)

    # update frame so view can update its coordinates
    view.frame = 2
    coordinates_dict = copy_coordinate_dict(view)
    nt.assert_equal(coordinates_dict[0].shape[0], 0)
    aa_eq(coordinates_dict[1], traj1[2].xyz)

    # hide 0, 1
    view.hide([0, 1])
    nt.assert_false(view._trajlist[0].shown)
    nt.assert_false(view._trajlist[1].shown)
    view.frame = 3
    coordinates_dict = copy_coordinate_dict(view)
    nt.assert_equal(coordinates_dict[0].shape[0], 0)
    nt.assert_equal(coordinates_dict[1].shape[0], 0)

    # slicing, show only component 1
    view[1].show()
    view.frame = 0
    nt.assert_false(view._trajlist[0].shown)
    nt.assert_true(view._trajlist[1].shown)
    coordinates_dict = copy_coordinate_dict(view)
    nt.assert_equal(coordinates_dict[0].shape[0], 0)
    aa_eq(coordinates_dict[1], traj1[0].xyz)

    # show all
    view[1].show()
    view[0].show()
    view.frame = 1
    nt.assert_true(view._trajlist[0].shown)
    nt.assert_true(view._trajlist[1].shown)
    coordinates_dict = copy_coordinate_dict(view)
    aa_eq(coordinates_dict[0], traj0[1].xyz)
    aa_eq(coordinates_dict[1], traj1[1].xyz)

    # hide all
    view[1].hide()
    view[0].hide()
    view.frame = 2
    nt.assert_false(view._trajlist[0].shown)
    nt.assert_false(view._trajlist[1].shown)
    coordinates_dict = copy_coordinate_dict(view)
    nt.assert_equal(coordinates_dict[0].shape[0], 0)
    nt.assert_equal(coordinates_dict[1].shape[0], 0)

def test_existing_js_files():
    from glob import glob
    jsfiles = glob(os.path.join(os.path.dirname(nv.__file__), 'static', '*js'))
    mapfiles = glob(os.path.join(os.path.dirname(nv.__file__), 'static', '*map'))

    nt.assert_equal(len(jsfiles), 2)
    nt.assert_equal(len(mapfiles), 1)

def test_add_struture_then_trajectory():
    view = nv.show_structure_file(get_fn('tz2.pdb'))
    view.loaded = True
    traj = pt.datafiles.load_trpcage()
    view.add_trajectory(traj)
    view.frame = 3
    coords = view.coordinates_dict[1].copy()
    aa_eq(coords, traj[3].xyz)
    view.loaded = False
    view.add_trajectory(traj)

def test_player_simple():
    traj = pt.datafiles.load_tz2()
    view = nv.show_pytraj(traj)
    nt.assert_false(view.player.sync_frame)

    # dummy
    component_slider = ipywidgets.IntSlider()
    repr_slider = ipywidgets.IntSlider()

    # dummy test
    player = nv.player.TrajectoryPlayer(view)
    player.smooth()
    player.camera = 'perspective'
    player.camera = 'orthographic'
    player.frame
    player.frame = 10 
    player.count
    player.sync_frame = False
    player.sync_frame = True
    player.parameters = dict(step=2)
    player._display()
    player._make_button_center()
    player._make_button_theme()
    player._make_button_reset_theme()
    player._make_widget_preference()
    player._show_download_image()
    player._make_button_url('dummy_url', description='dummy_url')
    player._show_website()
    player._make_button_qtconsole()
    player._make_text_picked()
    player._refresh(component_slider, repr_slider)
    player._make_widget_repr()
    player._make_resize_notebook_slider()
    player._make_button_export_image()
    player._make_repr_playground()
    player._make_drag_widget()
    player._make_spin_box()
    player._make_widget_picked()
    player._make_export_image_widget()
    player._make_theme_box()
    player._make_general_box()
    player._update_padding()
    player.on_spin_changed(change=dict(new=True))
    player.on_spin_x_changed(change=dict(new=1))
    player.on_spin_y_changed(change=dict(new=1))
    player.on_spin_z_changed(change=dict(new=1))
    player.on_spin_speed_changed(change=dict(new=0.5))
    player._real_time_update = True
    player._make_widget_repr()
    player.widget_component_slider
    player.widget_repr_slider
    player._create_all_tabs()
    player._create_all_widgets()
    player.widget_tab = None
    player._create_all_widgets()

def test_player_link_to_ipywidgets():
    traj = pt.datafiles.load_tz2()
    view = nv.show_pytraj(traj)

    int_text = IntText(2)
    float_text = BoundedFloatText(40, min=10)
    HBox([int_text, float_text])
    link((int_text, 'value'), (view.player, 'step'))
    link((float_text, 'value'), (view.player, 'delay'))

    nt.assert_equal(view.player.step, 2)
    nt.assert_equal(view.player.delay, 40)

    float_text.value = 100
    nt.assert_equal(view.player.delay, 100)

    float_text.value= 0.00
    # we set min=10
    nt.assert_equal(view.player.delay, 10)

def test_player_interpolation():
    view = default_view()

    view.player.interpolate = True
    nt.assert_equal(view.player.iparams.get('type'), 'linear')
    nt.assert_equal(view.player.iparams.get('step'), 1)

    def func():
        view.player.interpolate = True
        view.player.iparams = dict(type='spline_typos')
        view._set_coordinates(3)

    nt.assert_raises(ValueError, func())

def test_player_picked():
    view = nv.demo()
    s = dict(x=3)
    view.player.widget_picked = view.player._make_text_picked()
    view.picked = s
    nt.assert_equal(view.player.widget_picked.value, '{"x": 3}')

def test_widget_utils():
    box = HBox()
    i0 = IntText()
    i0._ngl_name = 'i0'
    i1 = IntText()
    i1._ngl_name = 'i1'
    box.children = [i0, i1]

    assert i0 is widget_utils.get_widget_by_name(box, 'i0')
    assert i1 is widget_utils.get_widget_by_name(box, 'i1')

    box.children = [i1, i0]
    assert i0 is widget_utils.get_widget_by_name(box, 'i0')
    assert i1 is widget_utils.get_widget_by_name(box, 'i1')

    nt.assert_equal(widget_utils.get_widget_by_name(box, 'i100'), None)

def test_theme():
    from nglview import theme
    theme.oceans16()
    theme.reset()
    theme._get_theme('oceans16.css')

def test_player_click_tab():
    view = nv.demo()
    gui = view.player._display()
    nt.assert_true(isinstance(gui, ipywidgets.Tab))

    for i, child in enumerate(gui.children):
        try:
            gui.selected_index = i
            nt.assert_true(isinstance(child, ipywidgets.Box))
        except TraitError:
            pass

def test_interpolate():
    # dummy test
    traj = pt.datafiles.load_tz2()
    ngl_traj = nv.PyTrajTrajectory(traj)
    interpolate.linear(0, 0.4, ngl_traj, step=1)

def dummy_test_to_increase_coverage():
    nv.__version__
