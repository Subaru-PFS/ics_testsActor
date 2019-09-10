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
            ('slit', '@(sm1|sm2|sm3|sm4)', self.slit),
            ('bia', '@(sm1|sm2|sm3|sm4)', self.bia),
            ('shutters', '@(sm1|sm2|sm3|sm4)', self.shutters),
            ('rexm', '@(sm1|sm2|sm3|sm4)', self.rexm),
            ('iis', '@(sm1|sm2|sm3|sm4)', self.iis),
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

    @singleShot
    def slit(self, cmd):
        cmdKeys = cmd.cmd.keywords
        smId = None
        smId = 'sm1' if 'sm1' in cmdKeys else smId
        smId = 'sm2' if 'sm2' in cmdKeys else smId
        smId = 'sm3' if 'sm3' in cmdKeys else smId
        smId = 'sm4' if 'sm4' in cmdKeys else smId

        try:
            self.controller.slit(cmd, smId=smId)
        except:
            cmd.warn('test=slit-%s,FAILED' % smId)
            raise

        cmd.finish('test=slit-%s,OK' % smId)

    @singleShot
    def bia(self, cmd):
        cmdKeys = cmd.cmd.keywords
        smId = None
        smId = 'sm1' if 'sm1' in cmdKeys else smId
        smId = 'sm2' if 'sm2' in cmdKeys else smId
        smId = 'sm3' if 'sm3' in cmdKeys else smId
        smId = 'sm4' if 'sm4' in cmdKeys else smId

        try:
            self.controller.bia(cmd, smId=smId)
        except:
            cmd.warn('test=bia-%s,FAILED' % smId)
            raise

        cmd.finish('test=bia-%s,OK' % smId)

    @singleShot
    def shutters(self, cmd):
        cmdKeys = cmd.cmd.keywords
        smId = None
        smId = 'sm1' if 'sm1' in cmdKeys else smId
        smId = 'sm2' if 'sm2' in cmdKeys else smId
        smId = 'sm3' if 'sm3' in cmdKeys else smId
        smId = 'sm4' if 'sm4' in cmdKeys else smId

        try:
            self.controller.shutters(cmd, smId=smId)
        except:
            cmd.warn('test=shutters-%s,FAILED' % smId)
            raise

        cmd.finish('test=shutters-%s,OK' % smId)

    @singleShot
    def rexm(self, cmd):
        cmdKeys = cmd.cmd.keywords
        smId = None
        smId = 'sm1' if 'sm1' in cmdKeys else smId
        smId = 'sm2' if 'sm2' in cmdKeys else smId
        smId = 'sm3' if 'sm3' in cmdKeys else smId
        smId = 'sm4' if 'sm4' in cmdKeys else smId

        try:
            self.controller.rexm(cmd, smId=smId)
        except:
            cmd.warn('test=rexm-%s,FAILED' % smId)
            raise

        cmd.finish('test=rexm-%s,OK' % smId)

    @singleShot
    def iis(self, cmd):
        cmdKeys = cmd.cmd.keywords
        smId = None
        smId = 'sm1' if 'sm1' in cmdKeys else smId
        smId = 'sm2' if 'sm2' in cmdKeys else smId
        smId = 'sm3' if 'sm3' in cmdKeys else smId
        smId = 'sm4' if 'sm4' in cmdKeys else smId

        try:
            self.controller.iis(cmd, smId=smId)
        except:
            cmd.warn('test=iis-%s,FAILED' % smId)
            raise

        cmd.finish('test=iis-%s,OK' % smId)
