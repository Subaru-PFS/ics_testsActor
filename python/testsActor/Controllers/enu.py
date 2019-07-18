import logging
import time


class enu(object):
    def __init__(self, actor, name, loglevel=logging.DEBUG):
        """This sets up the connections to/from the hub, the logger, and the twisted reactor.

        :param actor: spsaitActor
        :param name: controller name
        """

        self.actor = actor
        self.name = name

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(loglevel)

    def enuKey(self, smId, key):
        return self.actor.models['enu_%s' % smId].keyVarDict[key].getValue()

    def temps(self, cmd, smId):
        cmd.inform('text="starting temps-%s test' % smId)

        self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr='temps start')

        errorCode, errorMsg = self.enuKey(smId=smId, key='tempsStatus')

        if errorMsg != 'No error':
            raise ValueError('Temps status is not OK : %s' % errorMsg)

        cmd.inform('text="temps status OK, retrieving data ..."')

        data = []

        for i in range(3):
            self.actor.safeCall(cmd, actorName='enu_%s' % smId, cmdStr='temps status')
            row = self.enuKey(smId=smId, key='temps1') + self.enuKey(smId=smId, key='temps2')
            data.append(row)
            cmd.inform('temps=%s' % ','.join(['%.3f' % v for v in row]))
            time.sleep(3)

    def start(self, *args, **kwargs):
        pass

    def stop(self, *args, **kwargs):
        pass
