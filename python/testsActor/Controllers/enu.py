import logging
import time

import numpy as np


class enu(object):
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

    def temps(self, cmd, smId):
        cmd.inform('text="starting temps-%s test' % smId)

        self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr='temps start')

        errorCode, errorMsg = self.enuKey(smId=smId, key='tempsStatus')

        if errorMsg != 'No error':
            raise ValueError('Temps status is not OK : %s' % errorMsg)

        cmd.inform('text="temps status OK, retrieving data ..."')

        data = []

        for i in range(3):
            self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr='temps status')
            row = self.enuKey(smId=smId, key='temps1') + self.enuKey(smId=smId, key='temps2')
            data.append(row)
            cmd.inform('temps=%s' % ','.join(['%.3f' % v for v in row]))
            time.sleep(3)

    def slit(self, cmd, smId):
        cmd.inform('text="starting slit-%s test' % smId)

        self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr='slit start')

        position = self.enuKey(smId=smId, key='slitPosition')

        if position != 'home':
            raise ValueError('Slit should be at home')

        cmd.inform('text="slit status OK, testing motion ..."')

        for i in range(3):
            p = np.zeros(6)
            p[i] = 1
            cmdStr = f'X={p[0]}  Y={p[1]}  Z={p[2]}  U={p[3]}  V={p[4]}  W={p[5]}'
            cmd.inform(f'text="moving to {cmdStr}')
            self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr=f'slit move absolute {cmdStr}')
            self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr=f'slit status')

            c = np.array(self.enuKey(smId=smId, key='slit'))
            delta = np.sum(np.abs(p - c))
            cmd.inform(f'text="cumulate error={delta}')

            if delta > 0.05:
                raise RuntimeError('slit is not moving correctly')

        cmd.inform(f'text="moving to home')
        self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr='slit move home')

    def bia(self, cmd, smId):
        thr = 600
        cmd.inform('text="starting bia-%s test' % smId)

        self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr='biasha start')

        state = self.enuKey(smId=smId, key='bia')

        if state != 'off':
            raise ValueError('BIA should be switched off')

        cmd.inform('text="bia status OK, turning it on ..."')
        self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr='bia strobe off')
        self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr='bia on power=100')

        data = []
        for i in range(5):
            time.sleep(3)
            self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr='bia status')
            data.append(self.enuKey(smId=smId, key='photores'))
            cmd.inform('photores=%d,%d' % (data[-1][0], data[-1][1]))

        data = np.array(data)

        if np.mean(data[:, 0]) < thr:
            raise RuntimeError('photores 1 is not detecting light')
        if np.mean(data[:, 1]) < thr:
            raise RuntimeError('photores 2 is not detecting light')

        self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr='bia off')

    def shutters(self, cmd, smId, exptime=5.0):
        cmd.inform('text="starting shutters-%s test' % smId)

        self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr='biasha start')

        state = self.enuKey(smId=smId, key='shutters')

        if state != 'close':
            raise ValueError('shutters should be in closed position')

        cmd.inform('text="shutters status OK, testing exposure..."')

        for shutter in ['', 'blue', 'red']:
            time.sleep(1)
            cmd.inform(f'text="testing {shutter} shutter"')
            self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr=f'shutters expose exptime={exptime} {shutter}')
            delta = np.abs(self.enuKey(smId=smId, key='exptime') - exptime)
            if delta > 0.1:
                raise ValueError('exposure time is not set correctly')

            cmd.inform(f'text="exptime error = {np.round(delta, 3)} s"')

            if self.enuKey(smId=smId, key='transientTime') > 1.0:
                raise ValueError(f'shutter {shutter} speed is too slow')

    def rexm(self, cmd, smId):
        cmd.inform('text="starting rexm-%s test' % smId)

        self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr='rexm start', timeLim=180)

        position = self.enuKey(smId=smId, key='rexm')

        if position != 'low':
            raise ValueError('rexm should be in low position')

        cmd.inform('text="rexm status OK, testing motion..."')

        for position in ['med', 'low']:
            start = time.time()
            cmd.inform(f'text="going to {position} position"')
            self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr=f'rexm {position}', timeLim=180)
            end = time.time()
            time.sleep(3)
            self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr=f'rexm status')

            if self.enuKey(smId=smId, key='rexm') != position:
                raise ValueError(f'rexm should be in {position} position')

            cmd.inform(f'text="rexm motion completed in {round(end - start, 1)} s')

    def start(self, *args, **kwargs):
        pass

    def stop(self, *args, **kwargs):
        pass
