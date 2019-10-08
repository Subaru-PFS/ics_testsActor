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
            ('cooler', '<cam>', self.cooler),
            ('gauge', '<cam>', self.gauge),
            ('temps', '<cam>', self.temps),
            
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