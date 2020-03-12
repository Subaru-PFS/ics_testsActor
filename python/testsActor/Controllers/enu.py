import logging
import time

import numpy as np
from testsActor.utils import wait


class enu(object):
    lamps = ['hgar']
    biaThresh = 800
    iisThresh = 3
    probeNames = ['MOTOR_RDA',
                  'MOTOR_SHUTTER_B',
                  'MOTOR_SHUTTER_R',
                  'BIA_BOX_TOP',
                  'BIA_BOX_BOTTOM',
                  'FIBER_UNIT_HEXAPOD_BOTTOM',
                  'FIBER_UNIT_HEXAPOD_TOP',
                  'FIBER_UNIT_FIBER_FRAME_TOP',
                  'COLLIMATOR_FRAME_BOTTOM',
                  'COLLIMATOR_FRAME_TOP',
                  'BENCH_LEFT_TOP',
                  'BENCH_LEFT_BOTTOM',
                  'BENCH_RIGHT_TOP',
                  'BENCH_RIGHT_BOTTOM',
                  'BENCH_FAR_TOP',
                  'BENCH_FAR_BOTTOM',
                  'BENCH_NEAR_TOP',
                  'BENCH_NEAR_BOTTOM',
                  'BENCH_CENTRAL_TOP',
                  None]
    biaLabels = ['biaPhoto1', 'biaPhoto2']
    pduPort8 = [None, None, 'iisHgarVolts', 'iisHgarCurrent', 'iisHgarPower']

    def __init__(self, actor, name, loglevel=logging.DEBUG):
        """This sets up the connections to/from the hub, the logger, and the twisted reactor.

        :param actor: spsaitActor
        :param name: controller name
        """

        self.actor = actor
        self.name = name

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(loglevel)

    def enuKey(self, smId, key):
        return self.actor.models['enu_%s' % smId].keyVarDict[key].getValue()

    def slit(self, cmd, smId):

        cmd.inform('text="starting slit-%s test' % smId)
        self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr='slit start')

        if self.enuKey(smId=smId, key='slitPosition') != 'home':
            raise ValueError('Slit should be at home')

        cmd.inform('text="slit status OK, testing motion ..."')
        try:
            for i in range(self.actor.niter):
                wait()
                p = np.zeros(6)
                p[i] = 1
                cmdStr = f'X={p[0]}  Y={p[1]}  Z={p[2]}  U={p[3]}  V={p[4]}  W={p[5]}'
                cmd.inform(f'text="moving to {cmdStr}')
                self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr=f'slit move absolute {cmdStr}')
                self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr=f'slit status')

                c = np.array(self.enuKey(smId=smId, key='slit'))
                delta = np.sum(np.abs(p - c))
                cmd.inform(f'text="cumulate error={delta}')

                if delta > 0.05:
                    raise RuntimeError('slit is not moving correctly')
        finally:
            wait()
            cmd.inform(f'text="moving to home')
            self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr='slit move home')

    def temps(self, cmd, smId):
        cmd.inform('text="starting temps-%s test' % smId)

        self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr='temps start')

        errorCode, errorMsg = self.enuKey(smId=smId, key='tempsStatus')

        if errorMsg != 'No error':
            raise ValueError('Temps status is not OK : %s' % errorMsg)

        cmd.inform('text="temps status OK, retrieving data ..."')

        keys = ['temps1', 'temps2']
        labels = [f'{smId}__{probeName}' for probeName in enu.probeNames]

        df = self.actor.sampleData(cmd, actor='enu_%s' % smId, cmdStr='temps status', keys=keys, labels=labels)
        self.actor.genSample(cmd=cmd, df=df)

    def bia(self, cmd, smId):
        cmd.inform('text="starting bia-%s test' % smId)
        self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr='biasha start')

        if self.enuKey(smId=smId, key='bia') != 'off':
            raise ValueError('BIA should be switched off')

        cmd.inform('text="bia status OK, turning it on ..."')
        self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr='bia strobe off')
        self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr='bia on power=100')

        try:
            keys = ['photores']
            labels = [f'{smId}__{colname}' for colname in enu.biaLabels]

            df = self.actor.sampleData(cmd, actor='enu_%s' % smId, cmdStr='bia status', keys=keys, labels=labels)
            self.actor.genSample(cmd=cmd, df=df)

            for col in df.columns:
                if df[col].mean() < enu.biaThresh:
                    raise RuntimeError(f'{col} is not detecting light')

            cmd.inform('text="BIA OK, testing interlock..."')
            for shutter in ['', 'blue', 'red']:
                wait()
                cmd.inform(f'text="opening {shutter} shutter"')
                try:
                    self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr=f'shutters open {shutter}')
                except RuntimeError:
                    cmd.inform('text="INTERLOCK OK"')

        finally:
            self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr='biasha init')

    def shutters(self, cmd, smId, exptime=5.0):
        cmd.inform('text="starting shutters-%s test' % smId)
        self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr='biasha start')

        if self.enuKey(smId=smId, key='shutters') != 'close':
            raise ValueError('shutters should be in closed position')

        cmd.inform('text="shutters status OK, testing exposure..."')
        try:
            for shutter in ['', 'blue', 'red']:
                wait()
                cmd.inform(f'text="testing {shutter} shutter"')
                self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId,
                                    cmdStr=f'shutters expose exptime={exptime} {shutter}')
                delta = np.abs(self.enuKey(smId=smId, key='exptime') - exptime)
                if delta > 0.1:
                    raise ValueError('exposure time is not set correctly')

                cmd.inform(f'text="exptime error = {np.round(delta, 3)} s"')

                if self.enuKey(smId=smId, key='transientTime') > 1.0:
                    raise ValueError(f'shutter {shutter} speed is too slow')

            cmd.inform('text="Exposure OK, testing interlock..."')
            for shutter in ['', 'blue', 'red']:
                wait()
                cmd.inform(f'text="opening {shutter} shutter"')
                self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId,
                                    cmdStr=f'shutters open {shutter}')
                cmd.inform('text="turning BIA ON"')
                try:
                    self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr='bia on')
                    raise ValueError('bia on command should have failed !!')
                except RuntimeError:
                    cmd.inform('text="INTERLOCK OK"')
                    self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId,
                                        cmdStr=f'shutters close {shutter}')

        finally:
            self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr='biasha init')

    def rexm(self, cmd, smId):
        cmd.inform('text="starting rexm-%s test' % smId)
        self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr='rexm start', timeLim=180)

        if self.enuKey(smId=smId, key='rexm') != 'low':
            raise ValueError('rexm should be in low position')

        cmd.inform('text="rexm status OK, testing motion..."')

        for position in ['med', 'low']:
            wait()
            start = time.time()
            cmd.inform(f'text="going to {position} position"')
            self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr=f'rexm {position}', timeLim=180)
            end = time.time()
            self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr=f'rexm status')

            if self.enuKey(smId=smId, key='rexm') != position:
                raise ValueError(f'rexm should be in {position} position')

            cmd.inform(f'text="rexm motion completed in {round(end - start, 1)} s')

    def iis(self, cmd, smId):
        cmd.inform('text="starting iis-%s test' % smId)
        self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr='iis start')

        for lamp in enu.lamps:
            if self.enuKey(smId=smId, key=lamp):
                raise ValueError(f'{lamp} should be off')

        cmd.inform('text="iis status OK, warming up lamp..."')
        self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr='iis on=%s' % ','.join(enu.lamps))

        try:
            keys = ['pduPort8']
            labels = [f'{smId}__{colname}' for colname in enu.pduPort8]

            df = self.actor.sampleData(cmd, actor='enu_%s' % smId, cmdStr='power status', keys=keys, labels=labels)
            self.actor.genSample(cmd=cmd, df=df)

            power = df[np.array(df.columns[df.columns.str.contains('Power')])]
            for col in power.columns:
                if power[col].astype('float64').mean() < enu.iisThresh:
                    raise RuntimeError(f'{col} < {enu.iisThresh} !')

        finally:
            self.actor.safeCall(forUserCmd=cmd, actor='enu_%s' % smId, cmdStr='iis off=%s' % ','.join(enu.lamps))

    def start(self, *args, **kwargs):
        pass

    def stop(self, *args, **kwargs):
        pass
