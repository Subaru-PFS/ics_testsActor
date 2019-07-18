import logging
import time

import pandas as pd
from testsActor.utils import waitForTcpServer


class xcu(object):
    def __init__(self, actor, name, loglevel=logging.DEBUG):
        """This sets up the connections to/from the hub, the logger, and the twisted reactor.

        :param actor: spsaitActor
        :param name: controller name
        """

        self.actor = actor
        self.name = name

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(loglevel)

    def xcuKey(self, cam, key):
        return self.actor.models['xcu_%s' % cam].keyVarDict[key].getValue()

    def cooler(self, cmd, cam):
        cmd.inform('text="starting %s cooler test' % cam)

        name, state, volts, amps, watts = self.xcuKey(cam=cam, key='pcmPort3')

        if not int(state):
            cmd.inform('text="powering up cooler controller"')
            self.actor.safeCall(cmd, actorName='xcu_%s' % cam, cmdStr='power on cooler')

        cmd.inform('text="checking cooler tcp server"')
        waitForTcpServer(host='cooler-%s' % cam, port=10001)

        cmd.inform('text="connecting cooler controller"')
        self.actor.safeCall(cmd, actorName='xcu_%s' % cam, cmdStr='connect controller=cooler')

        self.actor.safeCall(cmd, actorName='xcu_%s' % cam, cmdStr='cooler status')

        state, errorMask, errorStr, minPower, maxPower, power = self.xcuKey(cam=cam, key='coolerStatus')

        if errorStr != 'OK':
            raise ValueError('Cooler status is not OK : %s' % errorStr)

        cmd.inform('text="cooler status OK, retrieving data ..."')

        data = []
        columns = ['setpoint', 'reject', 'tip', 'power']
        for i in range(3):
            self.actor.safeCall(cmd, actorName='xcu_%s' % cam, cmdStr='cooler status')
            row = self.xcuKey(cam=cam, key='coolerTemps')
            data.append(row)
            cmd.inform('coolerTemps=%s' % ','.join(['%.3f' % v for v in row]))
            time.sleep(3)

        data = pd.DataFrame(data=data, columns=columns)
        for col in columns:
            cmd.inform('%s=%.3f,%.3f' % (col, data[col].mean(), data[col].std()))

        self.actor.safeCall(cmd, actorName='xcu_%s' % cam, cmdStr='monitor controllers=cooler period=15')

    def start(self, *args, **kwargs):
        pass

    def stop(self, *args, **kwargs):
        pass
