#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import
from polymer.level1 import Level1_base
from polymer.block import Block
from netCDF4 import Dataset
import numpy as np
from warnings import warn
from datetime import datetime
from polymer.common import L2FLAGS
from polymer.utils import raiseflag
from os.path import basename, join, dirname
from collections import OrderedDict



class Level1_NETCDF(Level1_base):
    '''
    Reader for subsetted products in netcdf format
    (produced by SNAP)
    '''
    def __init__(self, filename, blocksize=(500, 400),
                 dir_smile=None, apply_land_mask=True):

        self.filename = filename
        self.root = Dataset(filename)
        self.blocksize = blocksize
        self.apply_land_mask = apply_land_mask

        # detect sensor
        title = self.root.getncattr('title')

        if 'MERIS' in title:
            self.sensor = 'MERIS'
            self.varnames = {
                    'SZA': 'sun_zenith',
                    'VZA': 'view_zenith',
                    'SAA': 'sun_azimuth',
                    'VAA': 'view_azimuth',
                    'ozone': 'ozone',
                    'zwind': 'zonal_wind',
                    'mwind': 'merid_wind',
                    'press': 'atm_press',
                    }
            BANDS_MERIS = [412, 443, 490, 510, 560,
                           620, 665, 681, 709, 754,
                           760, 779, 865, 885, 900]
            self.band_index = dict((b, i+1) for (i, b) in enumerate(BANDS_MERIS))

            # read detector wavelength and solar irradiance
            if dir_smile is None:
                dir_smile = join(dirname(dirname(__file__)), 'auxdata/meris/smile/v2/')

            if 'MERIS Full Resolution' in title:
                self.F0 = np.genfromtxt(join(dir_smile, 'sun_spectral_flux_fr.txt'), names=True)
                self.detector_wavelength = np.genfromtxt(join(dir_smile, 'central_wavelen_fr.txt'), names=True)
            elif 'MERIS Reduced Resolution' in title:
                self.F0 = np.genfromtxt(join(dir_smile, 'sun_spectral_flux_rr.txt'), names=True)
                self.detector_wavelength = np.genfromtxt(join(dir_smile, 'central_wavelen_rr.txt'), names=True)
            else:
                raise Exception('Invalid "{}"'.format(title))

        elif 'OLCI' in title:
            self.sensor = 'OLCI'
            self.varnames = {
                    'SZA': 'SZA',
                    'VZA': 'OZA',
                    'SAA': 'SAA',
                    'VAA': 'OAA',
                    'ozone': 'total_ozone',
                    'zwind': 'horizontal_wind_vector_1',
                    'mwind': 'horizontal_wind_vector_2',
                    'press': 'sea_level_pressure',
                    }
            BANDS_OLCI = [
                    400 , 412, 443 , 490, 510 , 560,
                    620 , 665, 674 , 681, 709 , 754,
                    760 , 764, 767 , 779, 865 , 885,
                    900 , 940, 1020]
            self.band_index = dict((b, i+1) for (i, b) in enumerate(BANDS_OLCI))

        else:
            raise Exception('Could not identify sensor from "{}"'.format(title))

        # get product shape
        totalheight = self.root.variables['latitude'].shape[0]
        totalwidth = self.root.variables['latitude'].shape[1]

        print('{} product, size is {}x{}'.format(self.sensor, totalheight, totalwidth))

        self.init_shape(
                totalheight=totalheight,
                totalwidth=totalwidth,
                sline=0, eline=-1,
                scol=0,  ecol=-1)

        self.init_date()

    def read_date(self, date):
        ''' parse a date in the format 04-JUL-2017 12:31:28.013924 '''
        date = date.replace('JAN', '01')
        date = date.replace('FEB', '02')
        date = date.replace('MAR', '03')
        date = date.replace('APR', '04')
        date = date.replace('MAY', '05')
        date = date.replace('JUN', '06')
        date = date.replace('JUL', '07')
        date = date.replace('AUG', '08')
        date = date.replace('SEP', '09')
        date = date.replace('OCT', '10')
        date = date.replace('NOV', '11')
        date = date.replace('DEC', '12')

        # remove the milliseconds
        date = date[:date.index('.')]

        return datetime.strptime(date, '%d-%m-%Y %H:%M:%S')


    def init_date(self):

        date1 = self.root.getncattr('start_date')
        date2 = self.root.getncattr('stop_date')

        date1 = self.read_date(date1)
        date2 = self.read_date(date2)

        self.dstart = date1
        self.dstop  = date2

        self.date = date1 + (date2 - date1)//2

    def get_bitmask(self, flags_dataset, flag_name, size, offset):
        flags = self.read_band(flags_dataset, size, offset)
        flag_meanings = self.root.variables[flags_dataset].getncattr('flag_meanings').split()
        flag_masks = self.root.variables[flags_dataset].getncattr('flag_masks')
        masks = dict(zip(flag_meanings, flag_masks))

        return flags & masks[flag_name] != 0


    def read_band(self, band_name, size, offset):

        (ysize, xsize) = size
        (yoffset, xoffset) = offset

        if band_name not in self.root.variables:
            for x in [str(x) for x in self.root.variables]:
                print('->', x)
            raise Exception('{} not in dataset'.format(band_name))

        var = self.root.variables[band_name]

        data = var[yoffset+self.sline:yoffset+self.sline+ysize,
                   xoffset+self.scol :xoffset+self.scol+xsize,
                  ]

        if 'ozone' in band_name:
            unit = var.getncattr('units')
            if unit == 'Kg.m-2':
                data /= 2.1415e-5  # convert kg/m2 to DU
            elif unit == 'DU':
                pass
            else:
                raise Exception('Error in ozone unit ({})'.format(unit))

        return data

    def read_block(self, size, offset, bands):

        nbands = len(bands)
        size3 = size + (nbands,)

        # initialize block
        block = Block(offset=offset, size=size, bands=bands)

        # read lat/lon
        block.latitude  = self.read_band('lat', size, offset)
        block.longitude = self.read_band('lon', size, offset)


        # read geometry
        block.sza = self.read_band(self.varnames['SZA'], size, offset)
        block.vza = self.read_band(self.varnames['VZA'], size, offset)
        block.saa = self.read_band(self.varnames['SAA'], size, offset)
        block.vaa = self.read_band(self.varnames['VAA'], size, offset)

        # read Rtoa
        block.Ltoa = np.zeros(size3) + np.NaN
        for iband, band in enumerate(bands):
            if self.sensor == 'MERIS':
                band_name = 'radiance_{}'.format(self.band_index[band])
            elif self.sensor == 'OLCI':
                band_name = 'Oa{:02d}_radiance'.format(self.band_index[band])
            else:
                raise Exception('Invalid sensor "{}"'.format(self.sensor))

            block.Ltoa[:,:,iband] = self.read_band(band_name, size, offset)

        # detector wavelength and solar irradiance
        block.wavelen = np.zeros(size3, dtype='float32') + np.NaN
        block.F0 = np.zeros(size3, dtype='float32') + np.NaN
        if self.sensor == 'MERIS':
            # read detector index
            detector_index = self.read_band('detector_index', size, offset)

            for iband, band in enumerate(bands):
                name = 'lam_band{}'.format(self.band_index[band]-1)   # 0-based
                block.wavelen[:,:,iband] = self.detector_wavelength[name][detector_index]

                name = 'E0_band{}'.format(self.band_index[band]-1)   # 0-based
                block.F0[:,:,iband] = self.F0[name][detector_index]

        else:  # OLCI
            for iband, band in enumerate(bands):
                block.wavelen[:,:,iband] = self.read_band('lambda0_band_{}'.format(self.band_index[band]), size, offset)
                block.F0[:,:,iband] = self.read_band('solar_flux_band_{}'.format(self.band_index[band]), size, offset)

        # read bitmask
        block.bitmask = np.zeros(size, dtype='uint16')
        if self.sensor == 'OLCI':
            if self.apply_land_mask:
                raiseflag(block.bitmask, L2FLAGS['LAND'], self.get_bitmask('quality_flags', 'land', size, offset))
            raiseflag(block.bitmask, L2FLAGS['L1_INVALID'], self.get_bitmask('quality_flags', 'invalid', size, offset))
            raiseflag(block.bitmask, L2FLAGS['L1_INVALID'], self.get_bitmask('quality_flags', 'cosmetic', size, offset))

        elif self.sensor == 'MERIS':
            if self.apply_land_mask:
                raiseflag(block.bitmask, L2FLAGS['LAND'], self.get_bitmask('l1_flags', 'LAND_OCEAN', size, offset))
            raiseflag(block.bitmask, L2FLAGS['L1_INVALID'], self.get_bitmask('l1_flags', 'INVALID', size, offset))
            raiseflag(block.bitmask, L2FLAGS['L1_INVALID'], self.get_bitmask('l1_flags', 'SUSPECT', size, offset))
            raiseflag(block.bitmask, L2FLAGS['L1_INVALID'], self.get_bitmask('l1_flags', 'COSMETIC', size, offset))

        # date
        block.jday = self.date.timetuple().tm_yday
        block.month = self.date.timetuple().tm_mon

        # read ancillary data
        block.ozone = self.read_band(self.varnames['ozone'], size, offset)
        zwind = self.read_band(self.varnames['zwind'], size, offset)
        mwind = self.read_band(self.varnames['mwind'], size, offset)
        block.wind_speed = np.sqrt(zwind**2 + mwind**2)
        block.surf_press = self.read_band(self.varnames['press'], size, offset)


        return block

    def attributes(self, datefmt):
        attr = OrderedDict()
        attr['l1_filename'] = self.filename
        attr['start_time'] = self.dstart.strftime(datefmt)
        attr['stop_time'] = self.dstop.strftime(datefmt)

        return attr

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

