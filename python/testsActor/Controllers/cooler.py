import logging

from actorcore.QThread import QThread


class cooler(QThread):
    def __init__(self, actor, name, loglevel=logging.DEBUG):
        """This sets up the connections to/from the hub, the logger, and the twisted reactor.

        :param actor: spsaitActor
        :param name: controller name
        """

        QThread.__init__(self, actor, name)

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(loglevel)

    def start(self, *args, **kwargs):
        QThread.start(self)

    def stop(self, *args, **kwargs):
        self.exit()

    def handleTimeout(self):
        if self.exitASAP:
            raise SystemExit()
