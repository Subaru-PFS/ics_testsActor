import logging
import os

from astropy.io import fits
from testsActor.utils import checkDuplicate


class sps(object):
    fitsKeys = ['SIMPLE', 'BITPIX', 'NAXIS', 'DETECTOR', 'W_VISIT', 'W_ARM', 'W_SPMOD', 'W_SITE',
                'EXPTIME', 'DARKTIME', 'DATE-OBS', 'W_PFDSGN',  'W_RVXCU', 'W_RVCCD', 'W_RVENU']

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

        self.actor.safeCall(forUserCmd=cmd, actor='iic',
                            cmdStr=f'bias cam={cam} name="R1 functest" comments="from testsActor"')

        [root, night, fname] = self.ccdKey(cam, 'filepath')
        filepath = os.path.join(root, night, 'sps', fname)

        hdulist = fits.open(filepath, "readonly")
        prihdr = hdulist[0].header

        cmd.inform(f'filepath={filepath}')

        if prihdr['DATA-TYP'] != 'BIAS':
            raise ValueError(f'DATA-TYP is incorrected {prihdr["DATA-TYP"]}')

        if prihdr['EXPTIME'] != 0:
            raise ValueError(f'EXPTIME is incorrected {prihdr["EXPTIME"]}')

        for key in sps.fitsKeys:
            gen = cmd.inform
            try:
                val = prihdr[key]
            except KeyError:
                val = 'Undefined'

            if 'Undefined' in str(val):
                missing.append(key)
                gen = cmd.warn

            gen(f'{key}={val}')

        if missing:
            raise ValueError(f'{", ".join(missing)} are missing')

        duplicates = checkDuplicate(list(prihdr.keys()))
        if duplicates:
            raise ValueError(f'{", ".join(duplicates)} duplicated')

    def dark(self, cmd, cam):
        missing = []
        exptime = 10.0
        cmd.inform('text="starting %s dark test' % cam)

        self.actor.safeCall(forUserCmd=cmd, actor='iic',
                            cmdStr=f'dark exptime={exptime} cam={cam} name="R1 functest" comments="from testsActor"')

        [root, night, fname] = self.ccdKey(cam, 'filepath')
        filepath = os.path.join(root, night, 'sps', fname)

        hdulist = fits.open(filepath, "readonly")
        prihdr = hdulist[0].header

        cmd.inform(f'filepath={filepath}')

        if prihdr['DATA-TYP'] != 'DARK':
            raise ValueError(f'DATA-TYP is incorrected {prihdr["DATA-TYP"]}')

        if abs(prihdr['EXPTIME'] - exptime) > 0.5:
            raise ValueError(f'EXPTIME is incorrected {prihdr["EXPTIME"]}')

        for key in sps.fitsKeys:
            gen = cmd.inform
            try:
                val = prihdr[key]
            except KeyError:
                val = 'Undefined'

            if 'Undefined' in str(val):
                missing.append(key)
                gen = cmd.warn

            gen(f'{key}={val}')

        if missing:
            raise ValueError(f'{", ".join(missing)} are missing')

        duplicates = checkDuplicate(list(prihdr.keys()))
        if duplicates:
            raise ValueError(f'{", ".join(duplicates)} duplicated')

    def fileIO(self, cmd, cam):
        cmd.inform('text="starting fileIO test')

    def start(self, *args, **kwargs):
        pass

    def stop(self, *args, **kwargs):
        pass
