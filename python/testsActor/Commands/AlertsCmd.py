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
            ('alerts', 'trigger', self.trigger),
            ('alerts', 'invalid', self.invalid),
            ('alerts', 'timeout', self.timeout),
        ]

        self.keys = keys.KeysDictionary("tests__alerts", (1, 1),
                                        )

    @property
    def controller(self):
        try:
            return self.actor.controllers['alerts']
        except KeyError:
            raise RuntimeError('alerts controller is not connected.')

    @singleShot
    def trigger(self, cmd):
        test = 'trigger'

        try:
            self.controller.trigger(cmd)
        except:
            cmd.warn(f'test=alerts-{test},FAILED')
            raise

        cmd.finish(f'test=alerts-{test},OK')

    @singleShot
    def invalid(self, cmd):
        test = 'invalid'

        try:
            self.controller.invalid(cmd)
        except:
            cmd.warn(f'test=alerts-{test},FAILED')
            raise

        cmd.finish(f'test=alerts-{test},OK')

    @singleShot
    def timeout(self, cmd):
        test = 'timeout'

        try:
            self.controller.timeout(cmd)
        except:
            cmd.warn(f'test=alerts-{test},FAILED')
            raise

        cmd.finish(f'test=alerts-{test},OK')
