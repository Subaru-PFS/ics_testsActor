#!/usr/bin/env python


import argparse
import logging

import actorcore.ICC


class OurActor(actorcore.ICC.ICC):
    def __init__(self, name, productName=None, configFile=None, logLevel=logging.INFO):
        # This sets up the connections to/from the hub, the logger, and the twisted reactor.
        #
        specIds = [i + 1 for i in range(4)]
        cams = ['b%i' % i for i in specIds] + ['r%i' % i for i in specIds]

        enus = ['enu_sm%i' % i for i in specIds]
        ccds = ['xcu_%s' % cam for cam in cams]

        actorcore.ICC.ICC.__init__(self, name,
                                   productName=productName,
                                   configFile=configFile,
                                   modelNames=enus + ccds)

        self.logger.setLevel(logLevel)

        self.everConnected = False

    def requireModel(self, actorName, cmd):
        """ Make sure that we are listening for a given actor keywords. """

        if actorName not in self.models.keys():
            cmd.inform(f"text='connecting model for actor {actorName}'")
            self.addModels([actorName])
            
    def safeCall(self, cmd, actorName, cmdStr, timeLim=60):
        cmdVar = self.cmdr.call(actor=actorName, cmdStr=cmdStr, forUserCmd=cmd, timeLim=timeLim)

        ret = cmdVar.replyList[-1].keywords.canonical(delimiter=';')

        if cmdVar.didFail:
            cmd.warn(ret)
            raise RuntimeError('cmd : %s %s has failed !!!' % (actorName, cmdStr))

        return ret

    def reloadConfiguration(self, cmd):
        cmd.inform('sections=%08x,%r' % (id(self.config),
                                         self.config))

    def connectionMade(self):
        if self.everConnected is False:
            logging.info("Attaching all controllers...")
            self.allControllers = [s.strip() for s in self.config.get(self.name, 'startingControllers').split(',')]
            self.attachAllControllers()
            self.everConnected = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='tests', type=str, nargs='?',
                        help='identity')
    parser.add_argument('--config', default=None, type=str, nargs='?',
                        help='configuration file to use')
    parser.add_argument('--logLevel', default=logging.INFO, type=int, nargs='?',
                        help='logging level')
    args = parser.parse_args()

    theActor = OurActor(args.name,
                        productName='testsActor',
                        configFile=args.config,
                        logLevel=args.logLevel)
    theActor.run()


if __name__ == '__main__':
    main()
