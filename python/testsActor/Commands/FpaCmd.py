#!/usr/bin/env python

import time

import opscore.protocols.keys as keys
import opscore.protocols.types as types

class FpaCmd(object):

    def __init__(self, actor):
        # This lets us access the rest of the actor.
        self.actor = actor

        # Declare the commands we implement. When the actor is started
        # these are registered with the parser, which will call the
        # associated methods when matched. The callbacks will be
        # passed a single argument, the parsed and typed command.
        #
        self.vocab = [
            ('fpaMotors', 'findRange <cam> [<current>] [<axis>]', self.findRange),
            ('fpaMotors', 'checkRepeats <cam> [<reps>] [<axis>] [<distance>] [<delay>]',
             self.checkRepeats),
        ]

        # Define typed command arguments for the above commands.
        self.keys = keys.KeysDictionary("test.test", (1, 1),
                                        keys.Key("cam", types.String(),
                                                 help='camera name, e.g. b2'),
                                        keys.Key("axis", types.Enum('a','b','c'), default=None,
                                                 help='axis name'),
                                        keys.Key("reps", types.Int(), default=10,
                                                 help='number of repetitions'),
                                        keys.Key("delay", types.Float(), default=60,
                                                 help='delay between repetitions'),
                                        keys.Key("distance", types.Int(), default=3000,
                                                 help='how far to move'),
                                        keys.Key("current", types.Int(),
                                                 help='motor current override'),
                                        
                                        )

    def safeCmd(self, cmd, actor, cmdString, timeLim=None):
        """ Send a command, raise Exception on failure.
        """
        
        cmdVar = self.actor.cmdr.call(actor=actor, cmdStr=cmdString,
                                      forUserCmd=cmd, timeLim=timeLim)
        if cmdVar.didFail:
            raise RuntimeError('command %s %r failed' % (actor, cmdString))
            # cmd.fail('text=%s' % (qstr('Failed to expose with %s' % (cmdString))))
            # return None

        return cmdVar

    def grabPositions(self, cmd, actor, legend, replyLevel='inform'):
        """ Fetch axis status, generate keywords, and return status.

        Args
        ----
        cmd : Command 
           where to send keywords
        actor : Actor
           keeper of the parts
        legend : str
           inserted into test keyword.

        Returns
        -------
        positions : three positions
        homeSwitches : three booleans
        farSwitches : three booleans
        """

        cmdFunc = getattr(cmd, replyLevel)
        model = self.actor.models[actor]
        self.safeCmd(cmd, actor, "motors status", timeLim=5)
        positions = []
        homeSwitches = []
        farSwitches = []
        for i in range(3):
            keyName = 'ccdMotor%d' % (i+1)
            posKey = getattr(model, keyName)
            homeSwitch = posKey[1]
            farSwitch = posKey[2]
            posVal = posKey[3]

            positions.append(posVal)
            homeSwitches.append(homeSwitch)
            farSwitches.append(farSwitch)
            cmdFunc('text="%s: %d %s %s %d"' % (legend, i+1,
                                                homeSwitch, farSwitch, posVal))

        return positions, homeSwitches, farSwitches
        
    def motorHome(self, cmd, cam, motor, doFinish=True):
        pass
    
    def checkRepeats(self, cmd):
        """ check how repeatable motion is. 

        1. home axes
        2. slew out the given distance
        3. slew back to near the home switch.
        4. inch onto the home switch. Report distance from home.
        5. cool off
        6. optionally repeat
        """

        keys = cmd.cmd.keywords
        cam = keys['cam'].values[0]
        axis = keys['axis'].values[0] if 'axis' in keys else None
        reps = keys['reps'].values[0] if 'reps' in keys else 1
        delay = keys['delay'].values[0] if 'delay' in keys else 60
        farDist = keys['distance'].values[0] if 'distance' in keys else 3000

        nearDist = 25
        actor = 'xcu_%s' % (cam)
        self.actor.requireModel(actor, cmd)
        
        if axis is None:
            allAxes = 'a', 'b', 'c'
            moveAxis = 'piston'
        else:
            allAxes = axis,
            moveAxis = axis

        cmd.inform('text="fpa checkRepeats starting %d-cycle repeatability test on %s:%s...."' % (reps, cam, ','.join(allAxes)))
        cmd.inform('text="fpa checkRepeats: initializing motors."')
        self.safeCmd(cmd, actor, "motors init", timeLim=5)

        didFail = False
        for i in range(reps):
            cmd.inform(f'text="fpa checkRepeats: homing for loop {i+1}/{reps}"')
            if axis is None:
                self.safeCmd(cmd, actor, "motors home", timeLim=60)
            else:
                self.safeCmd(cmd, actor, "motors home axes=%s" % (axis), timeLim=60)
            time.sleep(1)
            
            cmd.inform('text="fpa checkRepeats: driving to near far limit."')
            self.safeCmd(cmd, actor, "motors move %s=%d" % (moveAxis, farDist), timeLim=30)
            nearFar = self.grabPositions(cmd, actor, f'loop {i+1} nearFar', replyLevel='debug')
            if any(nearFar[-1]):
                cmd.fail('text="some axes hit the far switch: %s"' % (nearFar[-1]))
                return

            time.sleep(1)
            cmd.inform('text="fpa checkRepeats: driving to near home switch."')
            self.safeCmd(cmd, actor, "motors move %s=%d abs" % (moveAxis, nearDist), timeLim=30)
            nearHome = self.grabPositions(cmd, actor, f'loop {i+1} nearHome', replyLevel='debug')
            if any(nearHome[1]):
                cmd.fail('text="some axes hit the home switch: %s"' % (nearHome[1]))
                return
                
            time.sleep(1)
            for ax in allAxes:
                nTries = 3
                for tryHarder in range(nTries):
                    call = cmd.warn if (tryHarder > 0) else cmd.inform
                    call(f'text="fpa checkRepeats: inching {ax} onto home switch, try {tryHarder+1}/{nTries}"')
                    try:
                        self.safeCmd(cmd, actor, "motors toSwitch %s home set" % (ax), timeLim=30)
                        break
                    except:
                        lastPos = self.grabPositions(cmd, actor, 'toHome %d' % (i+1), replyLevel='warn')
                        cmd.warn('text="MISSED switch %d/%d times:"' % (tryHarder+1, nTries))
                        time.sleep(2)
                        if tryHarder == nTries-1:
                            raise RuntimeError("completely failed to reach home switch on %s: %s" % (ax, lastPos))
                        
            self.grabPositions(cmd, actor, 'loop %d onHome' % (i+1))
            
            cmd.inform(f'text="fpa checkRepeats: inching off home switch"')
            for ax in allAxes:
                self.safeCmd(cmd, actor, "motors toSwitch %s home clear" % (ax), timeLim=15)
            final = self.grabPositions(cmd, actor, f'loop {i+1} offHome')
            offsets = [final[0][a_i] - 100 for a_i in range(3)]
            if any([abs(o) > 2 for o in offsets]):
                call = cmd.warn
                didFail = True
            else:
                call = cmd.inform
            call('fpaMotorResiduals=%s,%d,%d,%d,%d' % (cam, i,
                                                       offsets[0], offsets[1], offsets[2]))
            if i < reps-1:
                cmd.inform('text="cooling down for %s seconds...."' % (delay))
                time.sleep(delay)
                
        cmd.inform(f'text="fpa checkRepeats: finished and homing"')
        self.safeCmd(cmd, actor, "motors home", timeLim=60)

        if didFail:
            cmd.fail('text="some residual was too high: look at the fpaMotorResiduals"')
        else:
            cmd.finish('text="done and homed"')

    def findRange(self, cmd):
        """ Measure full range of motor motion. 

        1. home axes
        2. slam into far limit
        3. inch off the far limit
        4. note position
        5. slew back near the home switch
        6. inch onto home switch.
        7. note position
        8. home

        """

        keys = cmd.cmd.keywords
        cam = keys['cam'].values[0]
        current = keys['current'].values[0] if 'current' in keys else None
        actor = 'xcu_%s' % (cam)
        axes = 'a','b','c'
        
        farDist = 5000          # Onto far switch
        nearDist = 25
        
        actor = 'xcu_%s' % (cam)
        self.actor.requireModel(actor, cmd)

        cmd.inform('text="fpa findRange: initializing and homing motors."')
        self.safeCmd(cmd, actor, "motors init", timeLim=5)
        time.sleep(1) 
        self.safeCmd(cmd, actor, "motors home", timeLim=60)
        time.sleep(1) 

        if current is not None:
            cmd.warn('test="overriding current to %d percent."' % (current))
            for ax_i, ax in enumerate(axes):
                self.safeCmd(cmd, actor, 'motors raw=aM%dm%dR' % (ax_i+1, current))

        cmd.inform('text="fpa findRange: driving past far limit."')
        self.safeCmd(cmd, actor, "motors move piston=%d" % (farDist), timeLim=30)
        pastFar = self.grabPositions(cmd, actor, 'pastFar')
        if not all(pastFar[-1]):
            cmd.fail('text="some axes are not on far limit: %s' % (pastFar[-1]))
            return
        time.sleep(1)
        
        cmd.inform('text="fpa findRange: inching off far limit."')
        for ax in axes:
            self.safeCmd(cmd, actor, "motors toSwitch %s far clear" % (ax), timeLim=60)
        offFar = self.grabPositions(cmd, actor, 'offFar')
        if any(offFar[-1]):
            cmd.fail('text="some axes are not off far limit: %s' % (offFar[-1]))
            return
        
        cmd.inform('text="fpa findRange: driving motors back to near home switch"')
        self.safeCmd(cmd, actor, "motors move piston=%d abs force" % (nearDist), timeLim=30)
        nearHome = self.grabPositions(cmd, actor, 'nearHome')
        if any(nearHome[1]):
            cmd.fail('text="some axes are on home limit: %s' % (nearHome[1]))
            return
        
        cmd.inform('text="fpa findRange: inching onto home switch."')
        for ax in axes:
            self.safeCmd(cmd, actor, "motors toSwitch %s home set" % (ax), timeLim=15)
        onHome = self.grabPositions(cmd, actor, 'onHome')
        if not all(onHome[1]):
            cmd.fail('text="some axes are not on home limit: %s' % (onHome[1]))
            return
        
        ranges = [offFar[0][i] - onHome[0][i] - 1 for i in range(3)]
        overshoot = [pastFar[0][i] - offFar[0][i] - 1 for i in range(3)]
        
        cmd.inform('text="fpa findRange: homing motors."')
        self.safeCmd(cmd, actor, "motors home", timeLim=60)
        cmd.inform('fpaMotorsOvershoot=%s,%d,%d,%d' % (cam, overshoot[0],
                                                       overshoot[1],
                                                       overshoot[2]))
        cmd.finish('fpaMotorsRange=%s,%d,%d,%d' % (cam,
                                                   ranges[0], ranges[1], ranges[2]))
