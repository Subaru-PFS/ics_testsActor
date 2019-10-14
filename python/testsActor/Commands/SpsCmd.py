#!/usr/bin/env python


import opscore.protocols.keys as keys
import opscore.protocols.types as types
from testsActor.utils import singleShot

class SpsCmd(object):
    def __init__(self, actor):
        # This lets us access the rest of the actor.
        self.actor = actor

        # Declare the commands we implement. When the actor is started
        # these are registered with the parser, which will call the
        # associated methods when matched. The callbacks will be
        # passed a single argument, the parsed and typed command.
        #
        self.vocab = [
            ('fileIO', '', self.fileIO),
            ('bias', '<cam>', self.bias),
            ('dark', '<cam>', self.dark),
        ]

        self.keys = keys.KeysDictionary("tests__sps", (1, 1),
                                        keys.Key("cam", types.String(),
                                                 help='camera to test'), )

    @property
    def controller(self):
        try:
            return self.actor.controllers['sps']
        except KeyError:
            raise RuntimeError('sps controller is not connected.')

    @singleShot
    def fileIO(self, cmd):
        cmdKeys = cmd.cmd.keywords

        try:
            self.controller.fileIO(cmd)
        except:
            cmd.warn('test=fileIO,FAILED')
            raise

        cmd.finish('test=fileIO,OK')

    @singleShot
    def bias(self, cmd):
        cmdKeys = cmd.cmd.keywords
        cam = cmdKeys['cam'].values[0]
        try:
            self.controller.bias(cmd, cam=cam)
        except:
            cmd.warn('test=bias-%s,FAILED' % cam)
            raise

        cmd.finish('test=bias-%s,OK' % cam)

    @singleShot
    def dark(self, cmd):
        cmdKeys = cmd.cmd.keywords
        cam = cmdKeys['cam'].values[0]
        try:
            self.controller.dark(cmd, cam=cam)
        except:
            cmd.warn('test=dark-%s,FAILED' % cam)
            raise

        cmd.finish('test=dark-%s,OK' % cam)