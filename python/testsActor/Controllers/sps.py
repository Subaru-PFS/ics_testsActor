import logging
import os

from astropy.io import fits
from pfs.utils.opdb import opDB
from testsActor.utils import checkDuplicate


class sps(object):
    fitsKeys = ['SIMPLE', 'BITPIX', 'NAXIS', 'DETECTOR', 'W_VISIT', 'W_ARM', 'W_SPMOD', 'W_SITE',
                'EXPTIME', 'DARKTIME', 'DATE-OBS', 'W_PFDSGN', 'W_RVXCU', 'W_RVCCD', 'W_RVENU']

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
                            cmdStr=f'bias cam={cam} name="{cam.upper()} functest" comments="from testsActor"')

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

        visit_set_id, = opDB.fetchone('select max(visit_set_id) from sps_sequence')
        seqtype, = opDB.fetchone(f'select sequence_type from sps_sequence where visit_set_id={visit_set_id}')
        if seqtype != 'biases':
            raise ValueError(f'sequence_type:{seqtype} !=biases')

        pfs_visit_id, = opDB.fetchone(f'select pfs_visit_id from visit_set where visit_set_id={visit_set_id}')
        if int(pfs_visit_id) != int(prihdr['W_VISIT']):
            raise ValueError(f'W_VISIT :{prihdr["W_VISIT"]} does not match opDB visit :{pfs_visit_id}')

        exptype, exptime, specNum, armNum = opDB.fetchone(
            f'select exp_type,exptime,sps_module_id,arm_num from sps_exposure inner join sps_visit on sps_exposure.pfs_visit_id='
            f'sps_visit.pfs_visit_id inner join sps_camera on sps_exposure.sps_camera_id = sps_camera.sps_camera_id '
            f'where sps_exposure.pfs_visit_id={pfs_visit_id}')

        if exptype != 'bias':
            raise ValueError(f'opDB exp_type:{exptype} !=bias')

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
                            cmdStr=f'dark exptime={exptime} cam={cam} name="{cam.upper()} functest" comments="from testsActor"')

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

        visit_set_id, = opDB.fetchone('select max(visit_set_id) from sps_sequence')
        seqtype, = opDB.fetchone(f'select sequence_type from sps_sequence where visit_set_id={visit_set_id}')
        if seqtype != 'darks':
            raise ValueError(f'sequence_type:{seqtype} !=darks')

        pfs_visit_id, = opDB.fetchone(f'select pfs_visit_id from visit_set where visit_set_id={visit_set_id}')
        if int(pfs_visit_id) != int(prihdr['W_VISIT']):
            raise ValueError(f'W_VISIT :{prihdr["W_VISIT"]} does not match opDB visit :{pfs_visit_id}')

        exptype, exp_time, specNum, armNum = opDB.fetchone(
            f'select exp_type,exptime,sps_module_id,arm_num from sps_exposure inner join sps_visit on sps_exposure.pfs_visit_id='
            f'sps_visit.pfs_visit_id inner join sps_camera on sps_exposure.sps_camera_id = sps_camera.sps_camera_id '
            f'where sps_exposure.pfs_visit_id={pfs_visit_id}')

        if exptype != 'dark':
            raise ValueError(f'opDB exp_type:{exptype} !=dark')

        if round(float(exp_time)) != round(exptime):
            raise ValueError(f'opDB exptime:{exp_time} does not match exptime:{exptime}')

        if int(specNum) != int(prihdr['W_SPMOD']):
            raise ValueError(f'opDB specNum:{specNum} !={prihdr["W_SPMOD"]}')

        if int(armNum) != int(prihdr['W_ARM']):
            raise ValueError(f'opDB armNum:{armNum} !={prihdr["W_ARM"]}')

        cmd.inform('text="opDB book-keeping OK')

    def fileIO(self, cmd, cam):
        cmd.inform('text="starting fileIO test')

    def start(self, *args, **kwargs):
        pass

    def stop(self, *args, **kwargs):
        pass
