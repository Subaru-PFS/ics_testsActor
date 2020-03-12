#!/usr/bin/env python

from functools import partial

import opscore.protocols.keys as keys
import opscore.protocols.types as types
from testsActor.utils import singleShot


class XcuCmd(object):
    testNames = ['power', 'gatevalve', 'turbo', 'ionpump', 'cooler', 'gauge', 'temps', 'heaters']

    def __init__(self, actor):
        # This lets us access the rest of the actor.
        self.actor = actor

        # Declare the commands we implement. When the actor is started
        # these are registered with the parser, which will call the
        # associated methods when matched. The callbacks will be
        # passed a single argument, the parsed and typed command.
        #
        self.vocab = []
        for testName in XcuCmd.testNames:
            testFunc = partial(self.testFunc, funcName=testName)
            setattr(self, testName, testFunc)
            self.vocab.append((testName, '<cam>', testFunc))

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
    def testFunc(self, cmd, funcName):
        cmdKeys = cmd.cmd.keywords
        cam = cmdKeys['cam'].values[0]
        self.actor.requireModel(f'xcu_{cam}', cmd)

        try:
            testFunc = getattr(self.controller, funcName)
            testFunc(cmd, cam=cam)
        except:
            cmd.warn(f'test={funcName}-{cam},FAILED')
            raise

        cmd.finish(f'test={funcName}-{cam},OK')
