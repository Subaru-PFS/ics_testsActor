#!/usr/bin/env python


import opscore.protocols.keys as keys
import opscore.protocols.types as types
from testsActor.utils import singleShot


class EnuCmd(object):
    def __init__(self, actor):
        # This lets us access the rest of the actor.
        self.actor = actor

        # Declare the commands we implement. When the actor is started
        # these are registered with the parser, which will call the
        # associated methods when matched. The callbacks will be
        # passed a single argument, the parsed and typed command.
        #
        self.vocab = [
            ('temps', '@(sm1|sm2|sm3|sm4)', self.temps),
        ]

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
    def temps(self, cmd):
        cmdKeys = cmd.cmd.keywords
        smId = None
        smId = 'sm1' if 'sm1' in cmdKeys else smId
        smId = 'sm2' if 'sm2' in cmdKeys else smId
        smId = 'sm3' if 'sm3' in cmdKeys else smId
        smId = 'sm4' if 'sm4' in cmdKeys else smId

        try:
            self.controller.temps(cmd, smId=smId)
        except:
            cmd.warn('test=temps-%s,FAILED' % smId)
            raise

        cmd.finish('test=temps-%s,OK' % smId)
