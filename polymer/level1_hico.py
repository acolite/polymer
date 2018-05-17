#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function, division, absolute_import
from polymer.block import Block
import numpy as np
import h5py
from datetime import datetime
from polymer.ancillary import Ancillary_NASA
from polymer.utils import raiseflag
from polymer.common import L2FLAGS
from numpy import interp
from collections import OrderedDict

bands_hico = [
    353,  358,  364,  370,  375,  381,  387,  393,  398,  404,  410,
    416,  421,  427,  433,  438,  444,  450,  456,  461,  467,  473,
    479,  484,  490,  496,  501,  507,  513,  519,  524,  530,  536,
    542,  547,  553,  559,  564,  570,  576,  582,  587,  593,  599,
    605,  610,  616,  622,  627,  633,  639,  645,  650,  656,  662,
    668,  673,  679,  685,  690,  696,  702,  708,  713,  719,  725,
    731,  736,  742,  748,  753,  759,  765,  771,  776,  782,  788,
    794,  799,  805,  811,  816,  822,  828,  834,  839,  845,  851,
    857,  862,  868,  874,  880,  885,  891,  897,  902,  908,  914,
    920,  925,  931,  937,  943,  948,  954,  960,  965,  971,  977,
    983,  988,  994, 1000, 1006, 1011, 1017, 1023, 1028, 1034, 1040,
    1046, 1051, 1057,1063, 1069, 1074, 1080]

K_OZ_HICO = { # from SeaDAS
     353:  0.000E+00, 358:  0.000E+00, 364:  0.000E+00, 370:  0.000E+00,
     375:  0.000E+00, 381:  0.000E+00, 387:  0.000E+00, 393:  0.000E+00,
     398:  2.382E-06, 404:  4.242E-05, 410:  1.681E-04, 416:  3.399E-04,
     421:  6.226E-04, 427:  1.007E-03, 433:  1.450E-03, 438:  2.290E-03,
     444:  3.178E-03, 450:  3.859E-03, 456:  5.440E-03, 461:  7.618E-03,
     467:  8.803E-03, 473:  1.101E-02, 479:  1.572E-02, 484:  1.929E-02,
     490:  2.101E-02, 496:  2.554E-02, 501:  3.419E-02, 507:  4.019E-02,
     513:  4.235E-02, 519:  4.745E-02, 524:  5.721E-02, 530:  6.836E-02,
     536:  7.497E-02, 542:  8.008E-02, 547:  8.636E-02, 553:  9.302E-02,
     559:  1.030E-01, 564:  1.149E-01, 570:  1.236E-01, 576:  1.257E-01,
     582:  1.222E-01, 587:  1.203E-01, 593:  1.254E-01, 599:  1.340E-01,
     605:  1.353E-01, 610:  1.268E-01, 616:  1.155E-01, 622:  1.062E-01,
     627:  9.817E-02, 633:  8.980E-02, 639:  8.098E-02, 645:  7.274E-02,
     650:  6.578E-02, 656:  5.945E-02, 662:  5.332E-02, 668:  4.736E-02,
     673:  4.158E-02, 679:  3.678E-02, 685:  3.278E-02, 690:  2.862E-02,
     696:  2.455E-02, 702:  2.133E-02, 708:  1.925E-02, 713:  1.781E-02,
     719:  1.595E-02, 725:  1.363E-02, 731:  1.183E-02, 736:  1.100E-02,
     742:  1.101E-02, 748:  1.003E-02, 753:  8.989E-03, 759:  7.996E-03,
     765:  7.430E-03, 771:  7.296E-03, 776:  7.254E-03, 782:  6.874E-03,
     788:  6.084E-03, 794:  5.236E-03, 799:  4.698E-03, 805:  4.590E-03,
     811:  4.705E-03, 816:  4.637E-03, 822:  4.144E-03, 828:  3.390E-03,
     834:  2.760E-03, 839:  2.506E-03, 845:  2.614E-03, 851:  2.813E-03,
     857:  2.769E-03, 862:  2.381E-03, 868:  1.856E-03, 874:  1.446E-03,
     880:  1.264E-03, 885:  1.267E-03, 891:  1.333E-03, 897:  1.340E-03,
     902:  1.216E-03, 908:  9.853E-04, 914:  7.445E-04, 920:  5.754E-04,
     925:  5.125E-04, 931:  5.433E-04, 937:  6.296E-04, 943:  6.936E-04,
     948:  6.570E-04, 954:  5.246E-04, 960:  3.707E-04, 965:  2.495E-04,
     971:  1.833E-04, 977:  1.775E-04, 983:  2.281E-04, 988:  3.012E-04,
     994:  3.282E-04, 1000: 2.760E-04, 1006: 1.864E-04, 1011: 1.133E-04,
     1017: 6.875E-05, 1023: 5.130E-05, 1028: 4.896E-05, 1034: 5.842E-05,
     1040: 7.574E-05, 1046: 8.988E-05, 1051: 8.934E-05, 1057: 7.555E-05,
     1063: 5.893E-05, 1069: 4.496E-05, 1074: 3.355E-05, 1080: 2.398E-05,
     }

K_NO2_HICO = {  # from SeaDAS
     353:  4.787E-19, 358:  5.126E-19, 364:  5.434E-19, 370:  5.655E-19,
     375:  5.858E-19, 381:  6.014E-19, 387:  6.150E-19, 393:  6.228E-19,
     398:  6.261E-19, 404:  6.172E-19, 410:  6.125E-19, 416:  5.966E-19,
     421:  5.886E-19, 427:  5.651E-19, 433:  5.445E-19, 438:  5.175E-19,
     444:  4.934E-19, 450:  4.721E-19, 456:  4.376E-19, 461:  4.214E-19,
     467:  3.825E-19, 473:  3.622E-19, 479:  3.389E-19, 484:  3.003E-19,
     490:  2.894E-19, 496:  2.600E-19, 501:  2.262E-19, 507:  2.252E-19,
     513:  2.007E-19, 519:  1.692E-19, 524:  1.671E-19, 530:  1.521E-19,
     536:  1.206E-19, 542:  1.168E-19, 547:  1.174E-19, 553:  9.460E-20,
     559:  7.551E-20, 564:  7.967E-20, 570:  7.570E-20, 576:  5.635E-20,
     582:  4.648E-20, 587:  4.964E-20, 593:  4.868E-20, 599:  3.776E-20,
     605:  2.750E-20, 610:  2.776E-20, 616:  3.138E-20, 622:  2.551E-20,
     627:  1.758E-20, 633:  1.426E-20, 639:  1.575E-20, 645:  1.747E-20,
     650:  1.435E-20, 656:  9.095E-21, 662:  6.469E-21, 668:  7.968E-21,
     673:  9.435E-21, 679:  7.739E-21, 685:  5.215E-21, 690:  3.478E-21,
     696:  2.720E-21, 702:  3.415E-21, 708:  4.506E-21, 713:  3.812E-21,
     719:  2.287E-21, 725:  1.477E-21, 731:  1.090E-21, 736:  1.235E-21,
     742:  1.646E-21, 748:  1.470E-21, 753:  1.263E-21, 759:  9.441E-22,
     765:  6.638E-22, 771:  4.860E-22, 776:  4.344E-22, 782:  4.663E-22,
     788:  4.942E-22, 794:  4.511E-22, 799:  3.412E-22, 805:  2.220E-22,
     811:  1.336E-22, 816:  8.411E-23, 822:  7.199E-23, 828:  8.476E-23,
     834:  1.075E-22, 839:  1.157E-22, 845:  1.023E-22, 851:  7.463E-23,
     857:  4.999E-23, 862:  3.491E-23, 868:  2.920E-23, 874:  3.226E-23,
     880:  3.937E-23, 885:  4.836E-23, 891:  5.454E-23, 897:  5.522E-23,
     902:  5.085E-23, 908:  4.357E-23, 914:  3.512E-23, 920:  2.738E-23,
     925:  1.975E-23, 931:  1.295E-23, 937:  6.818E-24, 943:  2.602E-24,
     948:  6.230E-25, 954:  0.000E+00, 960:  0.000E+00, 965:  0.000E+00,
     971:  0.000E+00, 977:  0.000E+00, 983:  0.000E+00, 988:  0.000E+00,
     994:  0.000E+00, 1000: 0.000E+00, 1006: 0.000E+00, 1011: 0.000E+00,
     1017: 0.000E+00, 1023: 0.000E+00, 1028: 0.000E+00, 1034: 0.000E+00,
     1040: 0.000E+00, 1046: 0.000E+00, 1051: 0.000E+00, 1057: 0.000E+00,
     1063: 0.000E+00, 1069: 0.000E+00, 1074: 0.000E+00, 1080: 0.000E+00,
     }

wav_hico = np.array([ # from SeaDAS
        352.200, 357.900, 363.700, 369.400, 375.100, 380.900,
        386.600, 392.300, 398.000, 403.800, 409.500, 415.200,
        420.950, 426.700, 432.400, 438.100, 443.900, 449.600,
        455.300, 461.050, 466.800, 472.500, 478.200, 484.000,
        489.700, 495.400, 501.100, 506.900, 512.600, 518.300,
        524.100, 529.800, 535.500, 541.200, 547.000, 552.700,
        558.400, 564.150, 569.900, 575.600, 581.300, 587.100,
        592.800, 598.500, 604.250, 610.000, 615.700, 621.400,
        627.200, 632.900, 638.600, 644.300, 650.100, 655.800,
        661.500, 667.300, 673.000, 678.700, 684.400, 690.200,
        695.900, 701.600, 707.350, 713.100, 718.800, 724.500,
        730.300, 736.000, 741.700, 747.100, 752.800, 758.550,
        764.300, 770.000, 775.700, 781.450, 787.200, 792.900,
        798.600, 804.400, 810.100, 815.800, 821.550, 827.300,
        833.000, 838.700, 844.500, 850.200, 855.900, 861.650,
        867.400, 873.100, 878.800, 884.550, 890.300, 896.000,
        901.750, 907.500, 913.200, 918.900, 924.650, 930.400,
        936.100, 941.800, 947.600, 953.300, 959.000, 964.750,
        970.500, 976.200, 981.900, 987.700, 993.400, 999.100,
        1004.850, 1010.600, 1016.300, 1022.000, 1027.750, 1033.500,
        1039.200, 1044.950, 1050.700, 1056.400, 1062.100, 1067.850,
        1073.600, 1079.300,
    ], dtype='float32')

F0_hico = np.array([    # from SeaDAS 7.3.2
            103.095,103.440,112.053,118.173,114.686,108.558,
            105.860,112.972,140.995,168.880,171.048,173.270,
            172.988,164.887,163.889,177.969,192.429,202.580,
            206.947,206.979,204.436,205.717,206.589,198.847,
            195.122,195.962,193.906,193.207,186.259,179.978,
            182.637,186.034,186.695,185.667,186.521,185.382,
            181.197,179.086,179.423,180.080,179.496,176.568,
            175.114,174.508,172.683,169.323,166.023,165.262,
            164.690,163.388,161.500,159.298,155.911,151.120,
            151.770,152.007,149.892,147.837,146.469,146.017,
            144.874,143.278,140.980,137.978,135.829,134.149,
            132.338,130.067,128.129,127.588,126.541,125.234,
            123.493,121.301,118.913,116.722,114.963,113.525,
            112.350,111.282,110.130,108.779,107.254,105.709,
            103.979,101.995,99.675,97.476,96.129,95.624,
            95.299,94.826,94.129,93.033,91.822,90.502,
            89.188,88.005,86.826,85.679,84.634,83.766,
            82.825,81.790,80.769,79.742,78.781,77.893,
            77.007,76.153,75.289,74.403,73.469,72.473,
            71.497,70.647,69.867,69.113,68.315,67.464,
            66.643,65.893,65.147,64.352,63.494,62.670,
            61.873,61.088
                ], dtype='float32')


class Level1_HICO(object):
    """
    HICO Level1 reader

    landmask:
        * None: no land mask [default]
        * A GSW instance (see gsw.py)
            Example: landmask=GSW(directory='/path/to/gsw_data/')
    """
    def __init__(self, filename, blocksize=200,
                 sline=0, eline=-1, scol=0, ecol=-1,
                 ancillary=None, landmask=None):
        self.h5 = h5py.File(filename)
        self.sensor = 'HICO'
        self.filename = filename
        self.landmask = landmask

        self.Lt = self.h5['products']['Lt']

        self.totalheight, self.totalwidth, nlam = self.Lt.shape
        self.blocksize = blocksize
        self.sline = sline
        self.scol = scol

        if ancillary is None:
            self.ancillary = Ancillary_NASA()
        else:
            self.ancillary = ancillary

        if eline < 0:
            self.height = self.totalheight
            self.height -= sline
            self.height += eline + 1
        else:
            self.height = eline-sline

        if ecol < 0:
            self.width = self.totalwidth
            self.width -= scol
            self.width += ecol + 1
        else:
            self.width = ecol - scol

        self.shape = (self.height, self.width)
        print('Initializing HICO product of size', self.shape)

        self.datetime = self.get_time()

        # initialize ancillary data
        self.ozone = self.ancillary.get('ozone', self.datetime)
        self.wind_speed = self.ancillary.get('wind_speed', self.datetime)
        self.surf_press = self.ancillary.get('surf_press', self.datetime)

        self.ancillary_files = OrderedDict()
        self.ancillary_files.update(self.ozone.filename)
        self.ancillary_files.update(self.wind_speed.filename)
        self.ancillary_files.update(self.surf_press.filename)

        self.init_landmask()


    def init_landmask(self):
        if not hasattr(self.landmask, 'get'):
            return

        lat = self.h5['navigation']['latitudes'][:,:]
        lon = self.h5['navigation']['longitudes'][:,:]

        self.landmask_data = self.landmask.get(lat, lon)


    def get_time(self):
        beg_date = self.h5['metadata']['FGDC']['Identification_Information']['Time_Period_of_Content'].attrs['Beginning_Date'].decode('ascii')
        beg_time = self.h5['metadata']['FGDC']['Identification_Information']['Time_Period_of_Content'].attrs['Beginning_Time'].decode('ascii')
        return datetime.strptime(beg_date + beg_time, '%Y%m%d%H%M%S')


    def read_block(self, size, offset, bands):
        nbands = len(bands)
        size3 = size + (nbands,)
        (ysize, xsize) = size
        (yoffset, xoffset) = offset
        SY = slice(offset[0]+self.sline, offset[0]+self.sline+size[0])
        SX = slice(offset[1]+self.scol , offset[1]+self.scol+size[1])

        block = Block(offset=offset, size=size, bands=bands)
        block.jday = self.datetime.timetuple().tm_yday
        block.month = self.datetime.timetuple().tm_mon

        block.latitude = self.h5['navigation']['latitudes'][SY, SX]
        block.longitude = self.h5['navigation']['longitudes'][SY, SX]
        block.sza = self.h5['navigation']['solar_zenith'][SY, SX]
        block.vza = self.h5['navigation']['sensor_zenith'][SY, SX]
        block.saa = self.h5['navigation']['solar_azimuth'][SY, SX]
        block.vaa = self.h5['navigation']['sensor_azimuth'][SY, SX]

        assert len(self.Lt.attrs['wavelengths']) == len(bands_hico)

        ibands = np.array([bands_hico.index(b) for b in bands])

        # read TOA
        block.Ltoa = np.zeros(size3) + np.NaN
        slope = self.Lt.attrs['slope']
        intercept = self.Lt.attrs['intercept']
        assert intercept == 0.
        block.Ltoa = slope * self.Lt[SY, SX, ibands]/10.  # convert

        # read bitmask
        block.bitmask = np.zeros(size, dtype='uint16')
        # flags = self.h5['quality']['flags'][SY, SX]
        # raiseflag(block.bitmask, L2FLAGS['LAND'], flags & 1 != 0)

        # read solar irradiance
        block.F0 = np.zeros(size3) + np.NaN
        block.F0[:,:,:] = F0_hico[None,None,ibands]

        # wavelength
        block.wavelen = np.zeros(size3, dtype='float32') + np.NaN
        block.wavelen[:,:,:] = wav_hico[None,None,ibands]
        block.cwavelen = wav_hico[ibands]

        # ancillary data
        block.ozone = np.zeros(size, dtype='float32')
        block.ozone[:] = self.ozone[block.latitude, block.longitude]
        block.wind_speed = np.zeros(size, dtype='float32')
        block.wind_speed[:] = self.wind_speed[block.latitude, block.longitude]
        block.surf_press = np.zeros(size, dtype='float32')
        block.surf_press[:] = self.surf_press[block.latitude, block.longitude]

        block.altitude = np.zeros(size, dtype='float32')

        if self.landmask is not None:
            raiseflag(block.bitmask, L2FLAGS['LAND'],
                      self.landmask_data[
                          yoffset+self.sline:yoffset+self.sline+ysize,
                          xoffset+self.scol:xoffset+self.scol+xsize,
                                         ])

        return block



    def blocks(self, bands_read):
        nblocks = int(np.ceil(float(self.height)/self.blocksize))
        for iblock in range(nblocks):
            # determine block size
            xsize = self.width
            if iblock == nblocks-1:
                ysize = self.height-(nblocks-1)*self.blocksize
            else:
                ysize = self.blocksize
            size = (ysize, xsize)

            # determine the block offset
            xoffset = 0
            yoffset = iblock*self.blocksize
            offset = (yoffset, xoffset)

            yield self.read_block(size, offset, bands_read)

    def attributes(self, datefmt):
        return OrderedDict()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


