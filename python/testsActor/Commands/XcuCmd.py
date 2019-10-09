#!/usr/bin/env python


import opscore.protocols.keys as keys
import opscore.protocols.types as types
from testsActor.utils import singleShot


class XcuCmd(object):
    def __init__(self, actor):
        # This lets us access the rest of the actor.
        self.actor = actor

        # Declare the commands we implement. When the actor is started
        # these are registered with the parser, which will call the
        # associated methods when matched. The callbacks will be
        # passed a single argument, the parsed and typed command.
        #
        self.vocab = [
            ('power', '<cam>', self.power),
            ('gatevalve', '<cam>', self.gatevalve),
            ('turbo', '<cam>', self.turbo),
            ('ionpump', '<cam>', self.ionpump),
            ('cooler', '<cam>', self.cooler),
            ('gauge', '<cam>', self.gauge),
            ('temps', '<cam>', self.temps),
            ('heaters', '<cam>', self.heaters),

        ]

        self.keys = keys.KeysDictionary("tests__xcu", (1, 1),
                                        keys.Key("cam", types.String(),
                                                 help='camera to test'), )

    @property
    def controller(self):
        try:
            return self.actor.controllers['xcu']
        except KeyError:
            raise RuntimeError('xcu controller is not connected.')

    @singleShot
    def power(self, cmd):
        cmdKeys = cmd.cmd.keywords
        cam = cmdKeys['cam'].values[0]
        try:
            self.controller.power(cmd, cam=cam)
        except:
            cmd.warn('test=power-%s,FAILED' % cam)
            raise

        cmd.finish('test=power-%s,OK' % cam)

    @singleShot
    def gatevalve(self, cmd):
        cmdKeys = cmd.cmd.keywords
        cam = cmdKeys['cam'].values[0]
        try:
            self.controller.gatevalve(cmd, cam=cam)
        except:
            cmd.warn('test=gatevalve-%s,FAILED' % cam)
            raise

        cmd.finish('test=gatevalve-%s,OK' % cam)

    @singleShot
    def turbo(self, cmd):
        cmdKeys = cmd.cmd.keywords
        cam = cmdKeys['cam'].values[0]
        try:
            self.controller.turbo(cmd, cam=cam)
        except:
            cmd.warn('test=turbo-%s,FAILED' % cam)
            raise

        cmd.finish('test=turbo-%s,OK' % cam)

    @singleShot
    def ionpump(self, cmd):
        cmdKeys = cmd.cmd.keywords
        cam = cmdKeys['cam'].values[0]
        try:
            self.controller.ionpump(cmd, cam=cam)
        except:
            cmd.warn('test=ionpump-%s,FAILED' % cam)
            raise

        cmd.finish('test=ionpump-%s,OK' % cam)

    @singleShot
    def cooler(self, cmd):
        cmdKeys = cmd.cmd.keywords
        cam = cmdKeys['cam'].values[0]
        try:
            self.controller.cooler(cmd, cam=cam)
        except:
            cmd.warn('test=cooler-%s,FAILED' % cam)
            raise

        cmd.finish('test=cooler-%s,OK' % cam)

    @singleShot
    def gauge(self, cmd):
        cmdKeys = cmd.cmd.keywords
        cam = cmdKeys['cam'].values[0]
        try:
            self.controller.gauge(cmd, cam=cam)
        except:
            cmd.warn('test=gauge-%s,FAILED' % cam)
            raise

        cmd.finish('test=gauge-%s,OK' % cam)

    @singleShot
    def temps(self, cmd):
        cmdKeys = cmd.cmd.keywords
        cam = cmdKeys['cam'].values[0]
        try:
            self.controller.temps(cmd, cam=cam)
        except:
            cmd.warn('test=temps-%s,FAILED' % cam)
            raise

        cmd.finish('test=temps-%s,OK' % cam)

    @singleShot
    def heaters(self, cmd):
        cmdKeys = cmd.cmd.keywords
        cam = cmdKeys['cam'].values[0]
        try:
            self.controller.heaters(cmd, cam=cam)
        except:
            cmd.warn('test=heaters-%s,FAILED' % cam)
            raise

        cmd.finish('test=heaters-%s,OK' % cam)
