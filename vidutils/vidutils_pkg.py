#============================================================
#                    Python Utilies Module
#                       18 August 2018
#============================================================
# A module meant to collect useful functions

import os, sys, struct, pickle, re
import inspect, warnings, pkg_resources, platform, math
from   functools  import wraps
from   contextlib import contextmanager
from   enum       import Enum
import numpy

system_name = platform.system()
if system_name != 'Linux':
    __all__=['__doc__','__version__','now','save','VideoWriter','VideoReader']
else: # allow the possibility of including some functions that only work in Linux
    __all__=['__doc__','__version__','now','save','VideoWriter','VideoReader']

def get_Docstring(dname):
    with open(pkg_resources.resource_filename('vidutils','DocStrings/'+dname),'r') as f:
        s = f.read()
    return s

__doc__=get_Docstring('ModuleDoc.txt')
__version__=pkg_resources.get_distribution('vidutils').version
#============================================================================
#                              Simple Utils
#============================================================================

def now(): # short and simple function to print time that is like a digital clock
    """Returns time formatted into a string"""
    return time.strftime('%I:%M:%S %p',time.localtime())

def save(fname, **kwargs): # a simple function to save a dictionary of useful items
    """Saves a list of kwargs into a file by the name specified by string fname using Pickle"""
    f = open(fname,'w+b')
    p = pickle.Pickler(f)
    p.dump(kwargs)
    f.close()

def load(fname): # function to load file created by utils.save()
    """Returns a dictionary of kwargs saved previously by save function"""
    if not os.path.isfile(fname): # error checking
        raise IOError('File not found')
    f = open(fname,'rb')
    p = pickle.Unpickler(f)
    data = p.load()
    f.close()
    return data
# can try making use of pool to speed up load greatly
# can save data segments and then use tarfile to combine them
# then when I read it, I count how many elements in archive to recover how many processes

#============================================================================
#                              Video Writer Class
#============================================================================

class VideoWriter:
    def __init__(self,fname,dim,fps,mode='w+b'):

        if (fname[-4:] != 'jmov')|(len(fname)<5):
            fname += '.jmov'
            m = re.search('\.',fname)
            if m is not None:
                warnings.warn('File extension is not .jmov',category=RuntimeWarning)

        self.dim = dim # dimension of frame
        self.fps = fps
        self.nframes = 0
        flen = 1
        for d in dim:
            flen *= d
        self.fmt = '<'+str(flen)+'B' # all unsigned 8 bit int
        self.open(fname,mode)

    def open(self,fname,mode):
        assert hasattr(self,'dim'), 'Must initialize FileWriter'

        if mode=='a':
            pass # do something interesting here
            # don't write header, just read, let dtype be optional here
        self.f = open(fname,mode)

        # header
        n = len(self.dim)

        num_b = 0
        self.nframes = 0
        num_b += self.f.write(struct.pack('<BQ',*(n,self.nframes)))
        num_b += self.f.write(struct.pack(f'<{n+1}I',*(self.fps,*self.dim)))

        return num_b # number of bytes written


    def write(self,arr):
        # write single frame
        assert not self.f.closed, 'File must be open'

        nb = 0

        nb += self.f.write(struct.pack(self.fmt,*arr.flatten()))

        self.nframes += 1 # need to define this
        current = self.f.tell()
        self.f.seek(struct.calcsize('<B'))
        nb += self.f.write(struct.pack('<Q',self.nframes))
        self.f.seek(current)

        return nb

    def close(self):
        self.f.close()
        return

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.f.close()


class VideoReader:
    def __init__(self,fname):
        # check if fname exists, or add '.jmov'

        self.open(fname)

    def open(self,fname):
        self.f = open(fname,'rb')
        self.f.seek(0)

        ndim, self.nframes = struct.unpack('<BQ',self.f.read(struct.calcsize('<BQ')))
        ret = struct.unpack(f'<{ndim+1}I',self.f.read(struct.calcsize(f'<{ndim+1}I')))
        self.fps = ret[0]
        self.dim = ret[1:]
        flen = 1
        for d in self.dim:
            flen *= d
        self.fmt = '<'+str(flen)+'B' # all unsigned 8 bit int
        self.current_frame = 0

        self.__header_len = struct.calcsize('<BQ')+struct.calcsize(f'<{ndim+1}I')
        self.__frame_len = struct.calcsize(self.fmt)

    def close(self):
        self.f.close()
        return

    def read(self,i=None):
        if i is None:
            i = self.current_frame
            assert self.current_frame < self.nframes, 'End of file'
        else:
            assert type(i)==int, 'Frame must be integer'
            assert i<self.nframes, 'Frame is outside of range'

        self.f.seek(self.__header_len+i*self.__frame_len)
        frame = numpy.array(struct.unpack(self.fmt,self.f.read(self.__frame_len))).astype(numpy.uint8).reshape(*self.dim)
        self.current_frame += 1
        return frame

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.f.close()

    def __iter__(self):
        self.current_frame = 0
        return self

    def __next__(self):
        if self.current_frame<self.nframes:
            frame = self.read()
            self.current_frame += 1
            return frame
        else:
            raise StopIteration
