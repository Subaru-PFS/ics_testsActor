import logging

from actorcore.QThread import QThread


class alerts(QThread):
    def __init__(self, actor, name, loglevel=logging.DEBUG):
        """This sets up the connections to/from the hub, the logger, and the twisted reactor.

        :param actor: spsaitActor
        :param name: controller name
        """
        QThread.__init__(self, actor, name, timeout=15)

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(loglevel)

    def generate(self, cmd):
        cmd.inform('keytest1=-99,10,23')
        cmd.inform('keytest2=23.3,nan')
        cmd.finish('keytest3=3.193e-05')

    def handleTimeout(self, cmd=None):
        if self.exitASAP:
            raise SystemExit()

        cmd = self.actor.bcast if cmd is None else cmd
        try:
            self.generate(cmd)
        except Exception as e:
            cmd.fail('text=%s' % self.actor.strTraceback(e))

    def start(self, *args, **kwargs):
        QThread.start(self)

    def stop(self, *args, **kwargs):
        self.exit()
