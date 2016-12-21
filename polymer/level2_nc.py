#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import
from polymer.level2 import Level2_file
from polymer.utils import safemove
from netCDF4 import Dataset
import tempfile
import numpy as np
from os.path import exists, dirname, join, basename
from shutil import rmtree


class Level2_NETCDF(Level2_file):
    '''
    Level2 in netCDF format

    filename: string
        if None, determine filename from level1 by using output directory
        outdir and extension ext
    outdir: output directory
    ext: output file extension
    overwrite: boolean
        overwrite existing file
    datasets: list or None
        list of datasets to include in level 2
        if None (default), use default_datasets defined in level2 module
    compress: activate compression
    tmpdir: path of temporary directory
    format: underlying file format as specified in netcdf's Dataset:
            one of 'NETCDF4', 'NETCDF4_CLASSIC', 'NETCDF3_CLASSIC' or 'NETCDF3_64BIT'
    '''
    def __init__(self,
                 filename=None,
                 ext='.nc',
                 tmpdir=None,
                 outdir=None,
                 overwrite=False,
                 datasets=None,
                 compress=True,
                 format='NETCDF4_CLASSIC',
                 ):
        self.filename = filename
        self.overwrite = overwrite
        self.datasets = datasets
        self.compress = compress
        self.outdir = outdir
        self.initialized = False
        self.varlist = {}
        self.ext = ext
        self.__tmpdir = tmpdir   # base tmp dir
        self.tmpdir = None       # sub dir, should be removed
        self.tmpfilename = None
        self.format=format

    def init(self, level1):
        super(self.__class__, self).init(level1)

        if self.__tmpdir is None:
            tmpdir = dirname(self.filename)
        else:
            tmpdir = tempfile.mkdtemp(dir=self.__tmpdir, prefix='level2_netcdf4_tmp_')
            self.tmpdir = tmpdir

        self.tmpfilename = join(tmpdir, basename(self.filename) + '.tmp')

        self.root = Dataset(self.tmpfilename, 'w', format=self.format)


    def write_block(self, name, data, S):
        '''
        write data into sds name with slice S
        '''
        assert data.ndim == 2
        if (data.dtype == np.uint16) and self.format == 'NETCDF4_CLASSIC':
            typ = np.int16
        else:
            typ = data.dtype
        if name not in self.varlist:
            self.varlist[name] = self.root.createVariable(
                    name, typ,
                    ['height', 'width'],
                    zlib=self.compress)

        self.varlist[name][S[0], S[1]] = data


    def write(self, block):
        (yoff, xoff) = block.offset
        (hei, wid) = block.size
        S = (slice(yoff,yoff+hei), slice(xoff,xoff+wid))

        if not self.initialized:

            self.root.createDimension('width', self.shape[1])
            self.root.createDimension('height', self.shape[0])
            self.initialized = True

        for d in self.datasets:

            # don't write dataset if not in block
            if d not in block.datasets():
                continue

            if block[d].ndim == 2:
                self.write_block(d, block[d], S)

            elif block[d].ndim == 3:
                for i, b in enumerate(block.bands):
                    sdsname = '{}{}'.format(d, b)
                    self.write_block(sdsname, block[d][:,:,i], S)
            else:
                raise Exception('Error ndim')

    def finish(self, params):
        # write attributes
        for k, v in params.items():
            self.root.setncatts({k: str(v)})
        self.root.close()

        # move to destination
        safemove(self.tmpfilename, self.filename)

    def attributes(self):
        attrs = {}
        attrs['l2_filename'] = self.filename
        attrs['l2_format'] = self.format
        return attrs

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()

    def cleanup(self):
        if self.tmpdir is not None:
            rmtree(self.tmpdir)
