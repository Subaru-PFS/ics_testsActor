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
        self.monitor = True

    def generate(self, cmd):
        cmd.inform('keytest1=163.2,165.35')
        cmd.inform('keytest2=1e-7')
        cmd.finish('keytest3=Closed,OK')

    def trigger(self, cmd):
        cmd.inform('keytest1=210.89,180.65')
        cmd.inform('keytest2=10.2')
        cmd.inform('keytest3=Open,"Status is not OK !! "')

    def invalid(self, cmd):
        cmd.inform('keytest1=nan,nan')
        cmd.inform('keytest2=nan')
        cmd.inform('keytest3=Closed,OK')

    def timeout(self, cmd):
        cmd.inform('text="stopping monitoring"')
        self.monitor = False

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
