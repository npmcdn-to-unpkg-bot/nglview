from __future__ import print_function, absolute_import

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

from .widget import NGLWidget
from . import datafiles

from .adaptor import (
    FileStructure,
    TextStructure,
    PdbIdStructure,
    MDTrajTrajectory,
    PyTrajTrajectory,
    ParmEdTrajectory,
    MDAnalysisTrajectory)

__all__ = [
    'demo',
    'show_pdbid',
    'show_url',
    'show_text',
    'show_simpletraj',
    'show_mdtraj',
    'show_pytraj',
    'show_mdanalysis',
    'show_parmed',
    'show_rdkit',
    'show_structure_file',]

def show_pdbid(pdbid, **kwargs):
    '''Show PDB entry.

    Examples
    --------
    >>> import nglview as nv
    >>> w = nv.show_pdbid("3pqr")
    >>> w
    '''
    structure = PdbIdStructure(pdbid)
    return NGLWidget(structure, **kwargs)

def show_url(url, **kwargs):
    kwargs2 = dict((k, v) for k, v in kwargs.items())
    view = NGLWidget()
    view.add_component(url, **kwargs2)
    return view

def show_text(text, **kwargs):
    """for development
    """
    structure = TextStructure(text)
    return NGLWidget(structure, **kwargs)

def show_structure_file(path, **kwargs):
    '''Show structure file. Allowed are text-based structure
    file formats that are by supported by NGL, including pdb,
    gro, mol2, sdf.

    Examples
    --------
    >>> import nglview as nv
    >>> w = nv.show_structure_file(nv.datafiles.GRO)
    >>> w
    '''
    structure = FileStructure(path)
    return NGLWidget(structure, **kwargs)


def show_simpletraj(traj, **kwargs):
    '''Show simpletraj trajectory and structure file.

    Examples
    --------
    >>> import nglview as nv
    >>> w = nv.show_simpletraj(nv.datafiles.GRO, nv.datafiles.XTC)
    >>> w
    '''
    return NGLWidget(traj, **kwargs)


def show_mdtraj(mdtraj_trajectory, **kwargs):
    '''Show mdtraj trajectory.

    Examples
    --------
    >>> import nglview as nv
    >>> import mdtraj as md
    >>> t = md.load(nv.datafiles.XTC, top=nv.datafiles.GRO)
    >>> w = nv.show_mdtraj(t)
    >>> w
    '''
    structure_trajectory = MDTrajTrajectory(mdtraj_trajectory)
    return NGLWidget(structure_trajectory, **kwargs)


def show_pytraj(pytraj_trajectory, **kwargs):
    '''Show pytraj trajectory.

    Examples
    --------
    >>> import nglview as nv
    >>> import pytraj as pt
    >>> t = pt.load(nv.datafiles.TRR, nv.datafiles.PDB)
    >>> w = nv.show_pytraj(t)
    >>> w
    '''
    trajlist = pytraj_trajectory if isinstance(pytraj_trajectory, (list, tuple)) else [pytraj_trajectory,]

    trajlist = [PyTrajTrajectory(traj) for traj in trajlist]
    return NGLWidget(trajlist, **kwargs)


def show_parmed(parmed_structure, **kwargs):
    '''Show pytraj trajectory.

    Examples
    --------
    >>> import nglview as nv
    >>> import parmed as pmd
    >>> t = pt.load_file(nv.datafiles.PDB)
    >>> w = nv.show_parmed(t)
    >>> w
    '''
    structure_trajectory = ParmEdTrajectory(parmed_structure)
    return NGLWidget(structure_trajectory, **kwargs)

def show_rdkit(rdkit_mol, **kwargs):
    '''Show rdkit's Mol.

    Parameters
    ----------
    rdkit_mol : rdkit.Chem.rdchem.Mol
    kwargs : additional keyword argument

    Examples
    --------
    >>> import nglview as nv
    >>> from rdkit import Chem
    >>> from rdkit.Chem import AllChem
    >>> m = Chem.AddHs(Chem.MolFromSmiles('COc1ccc2[C@H](O)[C@@H](COc2c1)N3CCC(O)(CC3)c4ccc(F)cc4'))
    >>> AllChem.EmbedMultipleConfs(m, useExpTorsionAnglePrefs=True, useBasicKnowledge=True)
    >>> view = nv.show_rdkit(m)
    >>> view

    >>> # add component m2
    >>> # create file-like object
    >>> fh = StringIO(Chem.MolToPDBBlock(m2))
    >>> view.add_component(fh, ext='pdb')

    >>> # load as trajectory, need to have ParmEd
    >>> view = nv.show_rdkit(m, parmed=True)
    '''
    from rdkit import Chem
    fh = StringIO(Chem.MolToPDBBlock(rdkit_mol))

    try:
        use_parmed = kwargs.pop("parmed")
    except KeyError:
        use_parmed = False

    if not use_parmed:
        view = NGLWidget()
        view.add_component(fh, ext='pdb', **kwargs)
        return view
    else:
        import parmed as pmd
        parm = pmd.load_rdkit(rdkit_mol)
        parm_nv = ParmEdTrajectory(parm)

        # set option for ParmEd
        parm_nv.only_save_1st_model = False

        # set option for NGL
        # wait for: https://github.com/arose/ngl/issues/126
        # to be fixed in NGLView
        # parm_nv.params = dict(firstModelOnly=True)
        return NGLWidget(parm_nv, **kwargs)

def show_mdanalysis(atomgroup, **kwargs):
    '''Show NGL widget with MDAnalysis AtomGroup.

    Can take either a Universe or AtomGroup as its data input.

    Examples
    --------
    >>> import nglview as nv
    >>> import MDAnalysis as mda
    >>> u = mda.Universe(nv.datafiles.GRO, nv.datafiles.XTC)
    >>> prot = u.select_atoms('protein')
    >>> w = nv.show_mdanalysis(prot)
    >>> w
    '''
    structure_trajectory = MDAnalysisTrajectory(atomgroup)
    return NGLWidget(structure_trajectory, **kwargs)

def demo(*args, **kwargs):
    from nglview import show_structure_file
    return show_structure_file(datafiles.PDB, *args, **kwargs)
