import logging
import os
import time

import fpga.geom as geom
import numpy as np
import testing.scopeProcedures as scopeTests
from astropy.io import fits
from pfs.utils.opdb import opDB
from testsActor.utils import checkDuplicate


def ampBiasLevel(hdulist):
    exp = geom.Exposure()
    exp.image = hdulist[1].data
    exp.header = hdulist[0].header
    exp = geom.Exposure(exp)
    ampIms, osIms, _ = exp.splitImage(doTrim=False)
    return [np.median(amp) for amp in ampIms]


def calcOffsets(filepath):
    hdulist = fits.open(filepath)
    meds = ampBiasLevel(hdulist)
    return scopeTests.calcOffsets1(meds)


class sps(object):
    fitsKeys = ['SIMPLE', 'BITPIX', 'NAXIS', 'DETECTOR', 'W_VISIT', 'W_ARM', 'W_SPMOD', 'W_SITE',
                'EXPTIME', 'DARKTIME', 'DATE-OBS', 'W_PFDSGN', 'W_RVXCU', 'W_RVCCD', 'W_RVENU', 'W_SBEMDT',
                'W_SFPADT', 'W_SHEXDT', 'W_SGRTDT']

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

    def isUndefined(self, hdr, key):
        """Check for undefined header keys"""
        try:
            val = hdr[key]
            if isinstance(val, float) and np.isnan(val):
                raise KeyError
            if isinstance(val, float) and val == float(9998):
                raise KeyError
            elif isinstance(val, int) and val == 9998:
                raise KeyError
            elif isinstance(val, str) and 'no available value' in val:
                raise KeyError

        except KeyError:
            val = 'Undefined'

        return val

    def bias(self, cmd, cam):
        missing = []
        cmd.inform('text="starting %s bias test' % cam)

        self.actor.safeCall(forUserCmd=cmd, actor='iic',
                            cmdStr=f'bias cam={cam} doTest name="{cam.upper()} functest" comments="from testsActor"')

        [root, night, fname] = self.ccdKey(cam, 'filepath')
        filepath = os.path.join(root, night, 'sps', fname)

        hdulist = fits.open(filepath, "readonly")
        prihdr = hdulist[0].header

        levels = ampBiasLevel(hdulist)
        self.genBiasLevel(cmd, levels)

        cmd.inform(f'filepath={filepath}')

        if prihdr['DATA-TYP'] != 'TEST':
            raise ValueError(f'DATA-TYP is incorrected {prihdr["DATA-TYP"]}')

        if prihdr['EXPTIME'] != 0:
            raise ValueError(f'EXPTIME is incorrected {prihdr["EXPTIME"]}')

        for key in sps.fitsKeys:
            if key == 'W_SGRTDT' and cam[0] in ['b', 'n']:
                # dont care about red grating in that case.
                continue

            gen = cmd.inform

            value = self.isUndefined(prihdr, key)
            if 'Undefined' in str(value):
                missing.append(key)
                gen = cmd.warn

            gen(f'{key}={value}')

        if missing:
            raise ValueError(f'{", ".join(missing)} are missing')

        duplicates = checkDuplicate(list(prihdr.keys()))
        if duplicates:
            raise ValueError(f'{", ".join(duplicates)} duplicated')

        visit_set_id, = opDB.fetchone('select max(visit_set_id) from iic_sequence')
        seqtype, = opDB.fetchone(f'select sequence_type from iic_sequence where visit_set_id={visit_set_id}')
        if seqtype != 'biases':
            raise ValueError(f'sequence_type:{seqtype} !=biases')

        pfs_visit_id, = opDB.fetchone(f'select pfs_visit_id from visit_set where visit_set_id={visit_set_id}')
        if int(pfs_visit_id) != int(prihdr['W_VISIT']):
            raise ValueError(f'W_VISIT :{prihdr["W_VISIT"]} does not match opDB visit :{pfs_visit_id}')

        exptype, exptime, specNum, armNum = opDB.fetchone(
            f'select exp_type,exptime,sps_module_id,arm_num from sps_exposure inner join sps_visit on sps_exposure.pfs_visit_id='
            f'sps_visit.pfs_visit_id inner join sps_camera on sps_exposure.sps_camera_id = sps_camera.sps_camera_id '
            f'where sps_exposure.pfs_visit_id={pfs_visit_id}')

        if exptype != 'test':
            raise ValueError(f'opDB exp_type : {exptype}!=test')

        if round(float(exptime)) != 0:
            raise ValueError(f'opDB exptime:{exptime} does not match exptime:0')

        if int(specNum) != int(prihdr['W_SPMOD']):
            raise ValueError(f'opDB specNum:{specNum} !={prihdr["W_SPMOD"]}')

        if int(armNum) != int(prihdr['W_ARM']):
            raise ValueError(f'opDB armNum:{armNum} !={prihdr["W_ARM"]}')

        cmd.inform('text="opDB book-keeping OK')

    def dark(self, cmd, cam):
        missing = []
        exptime = 10.0
        cmd.inform('text="starting %s dark test' % cam)

        self.actor.safeCall(forUserCmd=cmd, actor='iic',
                            cmdStr=f'dark exptime={exptime} cam={cam} doTest name="{cam.upper()} functest" comments="from testsActor"')

        [root, night, fname] = self.ccdKey(cam, 'filepath')
        filepath = os.path.join(root, night, 'sps', fname)

        hdulist = fits.open(filepath, "readonly")
        prihdr = hdulist[0].header

        levels = ampBiasLevel(hdulist)
        self.genBiasLevel(cmd, levels)

        cmd.inform(f'filepath={filepath}')

        if prihdr['DATA-TYP'] != 'TEST':
            raise ValueError(f'DATA-TYP is incorrected {prihdr["DATA-TYP"]}')

        if abs(prihdr['EXPTIME'] - exptime) > 0.5:
            raise ValueError(f'EXPTIME is incorrected {prihdr["EXPTIME"]}')

        for key in sps.fitsKeys:
            gen = cmd.inform
            value = self.isUndefined(prihdr, key)
            if 'Undefined' in str(value):
                missing.append(key)
                gen = cmd.warn

            gen(f'{key}={value}')

        if missing:
            raise ValueError(f'{", ".join(missing)} are missing')

        duplicates = checkDuplicate(list(prihdr.keys()))
        if duplicates:
            raise ValueError(f'{", ".join(duplicates)} duplicated')

        visit_set_id, = opDB.fetchone('select max(visit_set_id) from iic_sequence')
        seqtype, = opDB.fetchone(f'select sequence_type from iic_sequence where visit_set_id={visit_set_id}')
        if seqtype != 'darks':
            raise ValueError(f'sequence_type:{seqtype} !=darks')

        pfs_visit_id, = opDB.fetchone(f'select pfs_visit_id from visit_set where visit_set_id={visit_set_id}')
        if int(pfs_visit_id) != int(prihdr['W_VISIT']):
            raise ValueError(f'W_VISIT :{prihdr["W_VISIT"]} does not match opDB visit :{pfs_visit_id}')

        exptype, exp_time, specNum, armNum = opDB.fetchone(
            f'select exp_type,exptime,sps_module_id,arm_num from sps_exposure inner join sps_visit on sps_exposure.pfs_visit_id='
            f'sps_visit.pfs_visit_id inner join sps_camera on sps_exposure.sps_camera_id = sps_camera.sps_camera_id '
            f'where sps_exposure.pfs_visit_id={pfs_visit_id}')

        if exptype != 'test':
            raise ValueError(f'opDB exp_type : {exptype}!=test')

        if round(float(exp_time)) != round(exptime):
            raise ValueError(f'opDB exptime:{exp_time} does not match exptime:{exptime}')

        if int(specNum) != int(prihdr['W_SPMOD']):
            raise ValueError(f'opDB specNum:{specNum} !={prihdr["W_SPMOD"]}')

        if int(armNum) != int(prihdr['W_ARM']):
            raise ValueError(f'opDB armNum:{armNum} !={prihdr["W_ARM"]}')

        cmd.inform('text="opDB book-keeping OK')

    def fileIO(self, cmd, cam):
        cmd.inform('text="starting fileIO test')

    def tuneOffsets(self, cmd, cam, dryRun=False, checkOffsets=False):

        cmd.inform('text="starting %s tuneOffsets' % cam)
        m, r = [0] * 8, [-100] * 8
        cmd.inform('text="applying master: %s"' % (m))
        cmd.inform('text="applying refs  : %s"' % (r))

        self.actor.safeCall(forUserCmd=cmd, actor=f'ccd_{cam}',
                            cmdStr='fee setOffsets n=%d,%d,%d,%d,%d,%d,%d,%d p=%d,%d,%d,%d,%d,%d,%d,%d' % tuple(m + r))

        cmd.inform('text="taking bias ..."')
        self.actor.safeCall(forUserCmd=cmd, actor='iic',
                            cmdStr=f'bias cam={cam} name="{cam.upper()} tuneOffsets" comments="offsets cleared"')

        [root, night, fname] = self.ccdKey(cam, 'filepath')
        filepath = os.path.join(root, night, 'sps', fname)

        m, r = calcOffsets(filepath)
        cmd.inform('text="applying master: %s"' % (m))
        cmd.inform('text="applying refs  : %s"' % (r))
        vlist = tuple(m) + tuple(r)

        if not dryRun:
            self.actor.safeCall(forUserCmd=cmd, actor=f'ccd_{cam}',
                                cmdStr='fee setOffsets n=%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f '
                                       'p=%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f save' % vlist)
        else:
            cmd.inform('text="dryrun set, so not actually applying offsets"')
            return

        if checkOffsets:
            time.sleep(2)
            cmd.inform('text="checking bias levels"')
            cmd.inform('text="taking bias ..."')
            self.actor.safeCall(forUserCmd=cmd, actor='iic',
                                cmdStr=f'bias cam={cam} name="{cam.upper()} tuneOffsets" comments="after offsets were tuned"')

            [root, night, fname] = self.ccdKey(cam, 'filepath')
            filepath = os.path.join(root, night, 'sps', fname)
            hdulist = fits.open(filepath)
            levels = ampBiasLevel(hdulist)
            self.genBiasLevel(cmd, levels)

    def genBiasLevel(self, cmd, levels):
        cmd.inform('text="biasLevel should be ~1000 ADU within 15%"')
        cmd.inform(f"biasLevels={','.join([str(round(l)) for l in levels])}")
        cmd.inform(f"biasLevelRatio={','.join([str(round(l)) for l in np.array(levels) / 10])}")

    def start(self, *args, **kwargs):
        pass

    def stop(self, *args, **kwargs):
        pass
