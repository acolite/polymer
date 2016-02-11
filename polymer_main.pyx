
import numpy as np
cimport numpy as np

include "minimization.pyx"
include "water.pyx"


cdef class F(NelderMeadMinimizer):
    '''
    Defines the cost function minimized by Polymer
    Inherits from NelderMeadMinimizer which provides method minimize
    '''

    cdef float[:] Rprime
    cdef float[:] wav
    cdef WaterModel w

    def __init__(self, watermodel, *args, **kwargs):

        super(self.__class__, self).__init__(*args, **kwargs)

        self.w = watermodel

    cdef init(self, float[:] Rprime, float[:] wav):
        '''
        set the input parameters for the current pixel
        '''
        self.Rprime = Rprime
        self.wav = wav


    cdef float eval(self, float[:] x):
        '''
        Evaluate cost function for vector parameters x
        '''
        cdef float[:] Rw

        # calculate the. water reflectance for the current parameters
        Rw = self.w.calc_rho(x)

        return 0.


cdef class PolymerMinimizer:

    cdef F f
    cdef int Nparams

    def __init__(self, watermodel):

        self.Nparams = 2
        self.f = F(watermodel, self.Nparams)

    cdef loop(self, float [:,:,:] Rprime, float [:,:,:] wav):
        '''
        cython method which loops over the block pixels
        '''

        cdef int Nb = Rprime.shape[0]
        cdef int Nx = Rprime.shape[1]
        cdef int Ny = Rprime.shape[2]

        print 'processing a block of {}x{}x{}'.format(Nx, Ny, Nb)

        cdef float [:] x0 = np.ndarray(self.Nparams, dtype='float32')

        #
        # pixel loop
        #
        for i in range(Nx):
            for j in range(Ny):
                self.f.init(Rprime[:,i,j], wav[:,i,j])
                self.f.minimize(x0)

    def minimize(self, block):
        '''
        Call minimization code for a block
        (def method visible from python code)
        '''
        self.loop(block.Rprime, block.wavelen)

