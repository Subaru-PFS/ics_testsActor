import logging
import time

from testsActor.utils import waitForTcpServer


class xcu(object):
    probeLabels = ['detectorBox',
                   'mangin',
                   'spider',
                   'thermalSpreader',
                   'frontRing',
                   None, None, None, None, None,
                   'detectorStrap1',
                   'detectorStrap2']
    coolerLabels = ['coolerSetpoint', 'coolerReject', 'coolerTip', 'coolerPower']
    powerLabels = [None, None, '24VupsVolts', '24VupsCurrent', '24VupsPower'] + \
                  [None, None, '24VauxVolts', '24VauxCurrent', '24VauxPower'] + \
                  [None, None, 'motorsVolts', 'motorsCurrent', 'motorsPower'] + \
                  [None, None, 'gaugeVolts', 'gaugeCurrent', 'gaugePower'] + \
                  [None, None, 'coolerVolts', 'coolerCurrent', 'coolerPower'] + \
                  [None, None, 'tempsVolts', 'tempsCurrent', 'tempsPower'] + \
                  [None, None, 'beeVolts', 'beeCurrent', 'beePower'] + \
                  [None, None, 'feeVolts', 'feeCurrent', 'feePower'] + \
                  [None, None, 'interlockVolts', 'interlockCurrent', 'interlockPower'] + \
                  [None, None, 'heatersVolts', 'heatersCurrent', 'heatersPower']

    turboLabels = ['turboSpeed'] + ['turboVolts', 'turboCurrent', 'turboPower'] + \
                  ['turboBodyTemp', 'turboControllerTemp']
    interlockLabels = ['cryostatPressure', 'roughingPressure']
    ionpumpLabels = [None, 'ionpump1Volts', 'ionpump1Current', 'ionpump1Temps', 'ionpump1Pressure'] + \
                    [None, 'ionpump2Volts', 'ionpump2Current', 'ionpump2Temps', 'ionpump2Pressure']
    specIds = list(range(1, 5))
    otherCam = dict([(f'r{i}', f'b{i}') for i in specIds] + [(f'b{i}', f'r{i}') for i in specIds])
    heaterLabels = [None, None, None, None] + ['heatersCcdEnabled', 'heatersSpreaderEnabled'] + \
                   ['heatersCcdFraction', 'heatersSpreaderFraction']

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
        return self.actor.models[f'xcu_{cam}'].keyVarDict[key].getValue()

    def power(self, cmd, cam):
        cmd.inform(f'text="starting {cam} power test')

        cmd.inform('text="checking pcm tcp server"')
        waitForTcpServer(host=f'pcm-{cam}', port=1000)

        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='power status')

        for inputPower in ['pcmPower1', 'pcmPower2']:
            name, state, volts, amps, watts = self.xcuKey(cam=cam, key=inputPower)

            if state != 'OK':
                raise ValueError(f'{inputPower} state is not OK : {state}')

            if volts < 24:
                raise ValueError(f'{inputPower} voltage is too low {volts} < 24V : {state}')

        cmd.inform('text="power status OK, retrieving data ..."')

        keys = ['pcmPower1', 'pcmPower2'] + [f'pcmPort{i + 1}' for i in range(8)]
        labels = [f'{cam}__{colname}' for colname in xcu.powerLabels]

        df = self.actor.sampleData(cmd, actor=f'xcu_{cam}', cmdStr='power status', keys=keys, labels=labels)
        self.actor.genSample(cmd=cmd, df=df)

        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='monitor controllers=power period=60')

    def gatevalve(self, cmd, cam):
        cmd.inform(f'text="starting {cam} gatevalve test')
        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='gatevalve status')

        __, position, controlState = self.xcuKey(cam=cam, key='gatevalve')

        if position in ['Unknown', 'Invalid']:
            raise ValueError(f'gatevalve in {position} position')

        if controlState in ['Unknown', 'Invalid']:
            raise ValueError(f'gatevalve in {controlState} controlState')

        cmd.inform(f'{cam}__gatevalve={position},{controlState}')
        cmd.inform('text="gatevalve status OK, retrieving data ..."')

        df = self.actor.sampleData(cmd, actor=f'xcu_{cam}', cmdStr='gatevalve status',
                                   keys=['interlockPressures'],
                                   labels=[f'{cam}__{colname}' for colname in xcu.interlockLabels])
        self.actor.genSample(cmd=cmd, df=df)

        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='monitor controllers=gatevalve period=60')

        name, state, volts, amps, watts = self.xcuKey(cam=cam, key='pcmPort7')

        if not int(state):
            raise ValueError('interlock channel is not powered up')

    def turbo(self, cmd, cam):
        cmd.inform(f'text="starting {cam} turbo test')

        cmd.inform('text="connecting turbo controller"')
        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='connect controller=turbo')
        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='turbo status')

        cmd.inform('text="turbo status OK, retrieving data ..."')

        keys = ['turboSpeed', 'turboVAW', 'turboTemps']
        labels = [f'{cam}__{label}' for label in xcu.turboLabels]

        df = self.actor.sampleData(cmd, actor=f'xcu_{cam}', cmdStr='turbo status', keys=keys, labels=labels)
        self.actor.genSample(cmd=cmd, df=df)

        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='monitor controllers=turbo period=15')

    def ionpump(self, cmd, cam):
        cmd.inform(f'text="starting {cam} ionpump test')
        monitorOther = True
        try:
            self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{xcu.otherCam[cam]}',
                                cmdStr='monitor controllers=ionpump period=0')
            time.sleep(15)
        except:
            monitorOther = False

        cmd.inform('text="connecting ionpump controller"')
        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='connect controller=ionpump')
        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='ionpump status')

        for nb in range(2):
            __, __, errorStr = self.xcuKey(cam=cam, key=f'ionpump{nb + 1}Errors')
            if errorStr != 'OK':
                raise ValueError(f'ionpump status is not OK : {errorStr}')

        cmd.inform('text="ionpump status OK, retrieving data ..."')

        keys = ['ionpump1', 'ionpump2']
        labels = [f'{cam}__{label}' for label in xcu.ionpumpLabels]

        df = self.actor.sampleData(cmd, actor=f'xcu_{cam}', cmdStr='turbo status', keys=keys, labels=labels)
        self.actor.genSample(cmd=cmd, df=df)

        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='monitor controllers=ionpump period=15')
        if monitorOther:
            time.sleep(7.5)
            self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{xcu.otherCam[cam]}',
                                cmdStr='monitor controllers=ionpump period=15')

    def gauge(self, cmd, cam):
        cmd.inform(f'text="starting {cam} gauge test')

        cmd.inform('text="checking pcm tcp server"')
        waitForTcpServer(host=f'pcm-{cam}', port=1000)

        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='gauge status')

        pressure = self.xcuKey(cam=cam, key='pressure')
        cmd.inform('text="gauge status OK, retrieving data ..."')

        keys = ['pressure']
        labels = [f'{cam}__gauge']

        df = self.actor.sampleData(cmd, actor=f'xcu_{cam}', cmdStr='gauge status', keys=keys, labels=labels)
        self.actor.genSample(cmd=cmd, df=df)

        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='monitor controllers=gauge period=15')

        pressure = df[f'{cam}__gauge'].astype('float64').mean()
        if pressure < 0:
            raise ValueError(f'pressure : {pressure} is incorrect')

    def cooler(self, cmd, cam):
        cmd.inform(f'text="starting {cam} cooler test')

        name, state, volts, amps, watts = self.xcuKey(cam=cam, key='pcmPort3')

        if not int(state):
            cmd.inform('text="powering up cooler controller"')
            self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='power on cooler')

        cmd.inform('text="checking cooler tcp server"')
        waitForTcpServer(host=f'cooler-{cam}', port=10001)

        cmd.inform('text="connecting cooler controller"')
        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='connect controller=cooler')
        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='cooler status')

        state, errorMask, errorStr, minPower, maxPower, power = self.xcuKey(cam=cam, key='coolerStatus')

        if errorStr != 'OK':
            raise ValueError(f'Cooler status is not OK : {errorStr}')

        cmd.inform('text="cooler status OK, retrieving data ..."')

        keys = ['coolerTemps']
        labels = [f'{cam}__{label}' for label in xcu.coolerLabels]

        df = self.actor.sampleData(cmd, actor=f'xcu_{cam}', cmdStr='cooler status', keys=keys, labels=labels)
        self.actor.genSample(cmd=cmd, df=df)

        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='monitor controllers=cooler period=15')

    def temps(self, cmd, cam):
        cmd.inform(f'text="starting {cam} temps test')

        name, state, volts, amps, watts = self.xcuKey(cam=cam, key='pcmPort4')

        if not int(state):
            cmd.inform('text="powering up temps controller"')
            self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='power on temps')

        cmd.inform('text="checking temps tcp server"')
        waitForTcpServer(host=f'temps-{cam}', port=1024)

        cmd.inform('text="connecting temps controller"')
        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='connect controller=temps')
        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='temps status')

        temps = self.xcuKey(cam=cam, key='temps')
        cmd.inform('text="temps status OK, retrieving data ..."')

        keys = ['temps']
        labels = [f'{cam}__{label}' for label in xcu.probeLabels]

        df = self.actor.sampleData(cmd, actor=f'xcu_{cam}', cmdStr='temps status', keys=keys, labels=labels)
        self.actor.genSample(cmd=cmd, df=df)

        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='monitor controllers=temps period=15')

    def heaters(self, cmd, cam):
        cmd.inform(f'text="starting {cam} heaters test')

        name, state, volts, amps, watts = self.xcuKey(cam=cam, key='pcmPort4')
        if not int(state):
            raise ValueError('temps channel is not powered up')

        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='temps status')
        cmd.inform('text="heaters status OK, retrieving data ..."')

        keys = ['heaters']
        labels = [f'{cam}__{label}' for label in xcu.heaterLabels]

        df = self.actor.sampleData(cmd, actor=f'xcu_{cam}', cmdStr='heaters status', keys=keys, labels=labels)
        self.actor.genSample(cmd=cmd, df=df)

        self.actor.safeCall(forUserCmd=cmd, actor=f'xcu_{cam}', cmdStr='monitor controllers=heaters period=15')

        name, state, volts, amps, watts = self.xcuKey(cam=cam, key='pcmPort8')

        if not int(state):
            raise ValueError('heaters channel is not powered up')

    def start(self, *args, **kwargs):
        pass

    def stop(self, *args, **kwargs):
        pass
