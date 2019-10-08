import logging
import os
from astropy.io import fits

class sps(object):
    fitsKeys = ['SIMPLE', 'BITPIX', 'NAXIS', 'NAXIS1', 'NAXIS2', 'W_PFDSGN', 'IMAGETYP', 'DATE-OBS', 'EXPTIME']
    def __init__(self, actor, name, loglevel=logging.DEBUG):
        """This sets up the connections to/from the hub, the logger, and the twisted reactor.

        :param actor: spsaitActor
        :param name: controller name
        """

        self.actor = actor
        self.name = name

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(loglevel)

    def ccdKey(self, cam, key):
        return self.actor.models['ccd_%s' % cam].keyVarDict[key].getValue()

    def bias(self, cmd, cam):
        missing = []
        cmd.inform('text="starting %s bias test' % cam)

        self.actor.safeCall(forUserCmd=cmd, actor='sps', cmdStr=f'expose bias cam={cam}')

        [root, night, fname] = self.ccdKey(cam, 'filepath')
        filepath = os.path.join(root, 'pfs', night, fname)

        hdulist = fits.open(filepath, "readonly")
        prihdr = hdulist[0].header

        if prihdr['IMAGETYP'] !='bias':
            raise ValueError(f'IMAGETYP is incorrected {prihdr["IMAGETYP"]}')

        if prihdr['EXPTIME'] != 0:
            raise ValueError(f'EXPTIME is incorrected {prihdr["EXPTIME"]}')

        for key in sps.fitsKeys:
            gen = cmd.inform
            try:
                val = prihdr[key]
            except KeyError:
                val = 'Undefined'

            if 'Undefined' in val:
                missing.append(key)
                gen = cmd.warn
            
            gen(f'{key}={val}')
        
        if missing:
            raise RuntimeError(f'{", ".join(missing)} are missing')

    def dark(self, cmd, cam):
        missing = []
        exptime=10.0
        cmd.inform('text="starting %s dark test' % cam)

        self.actor.safeCall(forUserCmd=cmd, actor='sps', cmdStr=f'expose dark exptime={exptime} cam={cam}')

        [root, night, fname] = self.ccdKey(cam, 'filepath')
        filepath = os.path.join(root, 'pfs', night, fname)

        hdulist = fits.open(filepath, "readonly")
        prihdr = hdulist[0].header

        if prihdr['IMAGETYP'] != 'dark':
            raise ValueError(f'IMAGETYP is incorrected {prihdr["IMAGETYP"]}')

        if abs(prihdr['EXPTIME']-exptime)>0.5:
            raise ValueError(f'EXPTIME is incorrected {prihdr["EXPTIME"]}')

        for key in sps.fitsKeys:
            gen = cmd.inform
            try:
                val = prihdr[key]
            except KeyError:
                val = 'Undefined'

            if 'Undefined' in val:
                missing.append(key)
                gen = cmd.warn

            gen(f'{key}={val}')

        if missing:
            raise RuntimeError(f'{", ".join(missing)} are missing')

    def fileIO(self, cmd):
        cmd.inform('text="starting fileIO test')

    def start(self, *args, **kwargs):
        pass

    def stop(self, *args, **kwargs):
        pass
