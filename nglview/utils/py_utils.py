from __future__ import absolute_import
import os
import sys
import gzip
import bz2
from zipfile import ZipFile
import base64

__all__ = ['encode_base64', 'decode_base64',
           'seq_to_string', '_camelize',
           '_camelize_dict', 'get_colors_from_b64']

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

def _update_url(func):
    from nglview.default import NGL_BASE_URL
    func.__doc__ = func.__doc__.format(ngl_url=NGL_BASE_URL)
    return func

if PY3:
    string_types = str
else:
    string_types = basestring

def encode_base64(arr, dtype='f4'):
    arr = arr.astype(dtype)
    return base64.b64encode(arr.data).decode('utf8')

def decode_base64(data, shape, dtype='f4'):
    import numpy as np
    decoded_str = base64.b64decode(data)
    return np.frombuffer(decoded_str, dtype=dtype).reshape(shape)

def get_name(obj, kwargs):
    name = kwargs.pop('name', str(obj))
    if name.startswith('<nglview.'):
        name = name.split()[0].strip('<')
    return name

def get_repr_names_from_dict(repr_dict, component):
    """
    
    Parameters
    ----------
    """

    try:
        this_repr_dict = repr_dict['c' + str(component)]
        return [this_repr_dict[str(key)]['name'] for key in sorted(this_repr_dict.keys())]
    except KeyError:
        return []


def get_colors_from_b64(b64_image):
    """

    Examples
    --------
    >>> view.render_image()
    >>> get_colors_from_b64(view._image_data)

    Returns
    -------
    list of tuple 
    """
    # should install PIL
    # py3

    from PIL import Image
    import io, base64

    fp = io.BytesIO(base64.b64decode(b64_image))
    image = Image.open(fp)

    return image.getcolors(int(1E6))


def seq_to_string(seq):
    """e.g. convert [1, 3, 5] to "@1,3,5"
    """
    if isinstance(seq, string_types):
        return seq
    else:
        # assume 1D array
        return "@" + ",".join(str(s) for s in seq)

def _camelize(snake):
    """
    
    Examples
    --------
    >>> _camelize('remote_call')
    remoteCall
    >>> _camelize('remoteCall')
    remoteCall
    """
    words = snake.split('_')
    return words[0] + "".join(x.title() for x in words[1:])

def _camelize_dict(kwargs):
    return dict((_camelize(k), v) for k, v in kwargs.items())


class FileManager(object):
    """FileManager is for internal use.

    If file is in the current folder or subfoler, use filename
    If not, open content

    Parameters
    ----------
    src : str or file-like object
        filename
    compressed : None or bool, default None
        user can specify if the given file is compressed or not.
        if None, FileManager will detect based on file extension
    """
    def __init__(self, src, compressed=None, ext=None):
        self.src = src
        self.cwd = os.getcwd()
        self._compressed = compressed
        self._ext = ext
        self.unzip_backend = dict(gz=gzip, bz2=bz2, zip=ZipFile)

    def read(self, force_buffer=False):
        """prepare content to send to NGL
        """
        if self.use_filename and not force_buffer:
            return self.src
        else:
            if self.compressed_ext:
                return self.unzip_backend[self.compressed_ext].open(self.src).read()
            elif hasattr(self.src, 'read'):
                return self.src.read()
            else:
                if self.is_filename:
                    return open(self.src, 'rb').read()
                else:
                    return self.src

    @property
    def is_compressed(self):
        '''naive detection
        '''
        if self._compressed is None:
            if self.is_filename or self.is_url:
                return (self.src.endswith('gz') or
                        self.src.endswith('zip') or
                        self.src.endswith('bz2'))
            else:
                return False
        else:
            return self._compressed

    @property
    def compressed_ext(self):
        if self.is_compressed and self.is_filename:
            return self.src.split('.')[-1]
        else:
            return ''

    @property
    def use_filename(self):
        if hasattr(self.src, 'read'):
            return False
        else:
            if self.is_filename:
                cwd = os.getcwd()
                root_path = os.path.dirname(os.path.abspath(self.src))
                return (cwd in root_path)
            return False

    @property
    def ext(self):
        if self._ext is not None:
            return self._ext
        else:
            if hasattr(self.src, 'read') or (not self.is_filename and not self.is_url):
                raise ValueError("you must provide file extension if using file-like object or text content")
            if self.is_compressed:
                return self.src.split('.')[-2]
            else:
                return self.src.split('.')[-1]

    @property
    def is_filename(self):
        if hasattr(self.src, 'read'):
            return False
        else:
            return os.path.isfile(self.src)

    @property
    def is_binary(self):
        binary_exts = ["mmtf", "dcd", "mrc", "ccp4", "map", "dxbin"]
        return self.ext.lower() in binary_exts

    @property
    def is_url(self):
        return (isinstance(self.src, string_types) and
                ((self.src.startswith('http') or
                self.src.startswith('rcsb://'))))
