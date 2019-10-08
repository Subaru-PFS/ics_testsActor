import logging

from testsActor.utils import waitForTcpServer


class xcu(object):
    probeNames = ['detectorBox',
                  'mangin',
                  'spider',
                  'thermalSpreader',
                  'frontRing',
                  None, None, None, None, None,
                  'detectorStrap1',
                  'detectorStrap2']
    coolerLabels = ['coolerSetpoint', 'coolerReject', 'coolerTip', 'coolerPower']

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
            self.actor.safeCall(forUserCmd=cmd, actor='xcu_%s' % cam, cmdStr='power on cooler')

        cmd.inform('text="checking cooler tcp server"')
        waitForTcpServer(host='cooler-%s' % cam, port=10001)

        cmd.inform('text="connecting cooler controller"')
        self.actor.safeCall(forUserCmd=cmd, actor='xcu_%s' % cam, cmdStr='connect controller=cooler')
        self.actor.safeCall(forUserCmd=cmd, actor='xcu_%s' % cam, cmdStr='cooler status')

        state, errorMask, errorStr, minPower, maxPower, power = self.xcuKey(cam=cam, key='coolerStatus')

        if errorStr != 'OK':
            raise ValueError('Cooler status is not OK : %s' % errorStr)

        cmd.inform('text="cooler status OK, retrieving data ..."')

        keys = ['coolerTemps']
        labels = [f'{cam}__{label}' for label in xcu.coolerLabels]

        df = self.actor.sampleData(cmd, actor='xcu_%s' % cam, cmdStr='cooler status', keys=keys, labels=labels)
        self.actor.genSample(cmd=cmd, df=df)

        self.actor.safeCall(forUserCmd=cmd, actor='xcu_%s' % cam, cmdStr='monitor controllers=cooler period=15')

    def gauge(self, cmd, cam):
        cmd.inform('text="starting %s gauge test' % cam)

        cmd.inform('text="checking pcm tcp server"')
        waitForTcpServer(host='pcm-%s' % cam, port=1000)

        self.actor.safeCall(forUserCmd=cmd, actor='xcu_%s' % cam, cmdStr='gauge status')

        pressure = self.xcuKey(cam=cam, key='pressure')
        cmd.inform('text="gauge status OK, retrieving data ..."')

        keys = ['pressure']
        labels = [f'{cam}__gauge']

        df = self.actor.sampleData(cmd, actor='xcu_%s' % cam, cmdStr='gauge status', keys=keys, labels=labels)
        self.actor.genSample(cmd=cmd, df=df)

        self.actor.safeCall(forUserCmd=cmd, actor='xcu_%s' % cam, cmdStr='monitor controllers=gauge period=15')

    def temps(self, cmd, cam):
        cmd.inform('text="starting %s temps test' % cam)

        name, state, volts, amps, watts = self.xcuKey(cam=cam, key='pcmPort4')

        if not int(state):
            cmd.inform('text="powering up temps controller"')
            self.actor.safeCall(forUserCmd=cmd, actor='xcu_%s' % cam, cmdStr='power on temps')

        cmd.inform('text="checking temps tcp server"')
        waitForTcpServer(host='temps-%s' % cam, port=1024)

        cmd.inform('text="connecting temps controller"')
        self.actor.safeCall(forUserCmd=cmd, actor='xcu_%s' % cam, cmdStr='connect controller=temps')
        self.actor.safeCall(forUserCmd=cmd, actor='xcu_%s' % cam, cmdStr='temps status')

        temps = self.xcuKey(cam=cam, key='temps')
        cmd.inform('text="temps status OK, retrieving data ..."')

        keys = ['temps']
        labels = [f'{cam}__{label}' for label in xcu.probeNames]

        df = self.actor.sampleData(cmd, actor='xcu_%s' % cam, cmdStr='temps status', keys=keys, labels=labels)
        self.actor.genSample(cmd=cmd, df=df)

        self.actor.safeCall(forUserCmd=cmd, actor='xcu_%s' % cam, cmdStr='monitor controllers=temps period=15')

    def start(self, *args, **kwargs):
        pass

    def stop(self, *args, **kwargs):
        pass
