#!/usr/bin/env python


from functools import partial

import opscore.protocols.keys as keys
import opscore.protocols.types as types
from testsActor.utils import singleShot


class EnuCmd(object):
    testNames = ['temps', 'slit', 'bia', 'shutters', 'rexm', 'iis']

    def __init__(self, actor):
        # This lets us access the rest of the actor.
        self.actor = actor

        # Declare the commands we implement. When the actor is started
        # these are registered with the parser, which will call the
        # associated methods when matched. The callbacks will be
        # passed a single argument, the parsed and typed command.
        #
        self.vocab = []
        for testName in EnuCmd.testNames:
            testFunc = partial(self.testFunc, funcName=testName)
            setattr(self, testName, testFunc)
            self.vocab.append((testName, '@(sm1|sm2|sm3|sm4)', testFunc))

        self.keys = keys.KeysDictionary("tests__enu", (1, 1),
                                        keys.Key("smId", types.Int(),
                                                 help='spectrograph to test'), )

    @property
    def controller(self):
        try:
            return self.actor.controllers['enu']
        except KeyError:
            raise RuntimeError('enu controller is not connected.')

    @singleShot
    def testFunc(self, cmd, funcName):
        cmdKeys = cmd.cmd.keywords
        smId = None
        smId = 'sm1' if 'sm1' in cmdKeys else smId
        smId = 'sm2' if 'sm2' in cmdKeys else smId
        smId = 'sm3' if 'sm3' in cmdKeys else smId
        smId = 'sm4' if 'sm4' in cmdKeys else smId
        self.actor.requireModel(f'enu_{smId}', cmd)

        try:
            testFunc = getattr(self.controller, funcName)
            testFunc(cmd, smId=smId)
        except:
            cmd.warn(f'test={funcName}-{smId},FAILED')
            raise

        cmd.finish(f'test={funcName}-{smId},OK')
