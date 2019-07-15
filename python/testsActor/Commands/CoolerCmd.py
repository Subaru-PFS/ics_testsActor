#!/usr/bin/env python


import opscore.protocols.keys as keys
import opscore.protocols.types as types
from enuActor.utils.wrap import threaded


class CoolerCmd(object):
    def __init__(self, actor):
        # This lets us access the rest of the actor.
        self.actor = actor

        # Declare the commands we implement. When the actor is started
        # these are registered with the parser, which will call the
        # associated methods when matched. The callbacks will be
        # passed a single argument, the parsed and typed command.
        #
        self.name = "cooler"
        self.vocab = [
            ('cooler', '<cam>', self.test),
        ]

        self.keys = keys.KeysDictionary("tests__cooler", (1, 1),
                                        keys.Key("cam", types.String(),
                                                 help='camera to test'), )

    @property
    def controller(self):
        try:
            return self.actor.controllers[self.name]
        except KeyError:
            raise RuntimeError('%s controller is not connected.' % self.name)

    @threaded
    def test(self, cmd):
        cmdKeys = cmd.cmd.keywords
        cam = cmdKeys['cam'].values[0]
        self.controller.test(cmd, cam=cam)

        cmd.finish('text="cooler %s OK..."' % cam)
