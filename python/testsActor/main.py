#!/usr/bin/env python


import argparse
import logging

import actorcore.ICC
import numpy as np
import pandas as pd

from testsActor.utils import newRow, wait

class OurActor(actorcore.ICC.ICC):
    niter = 3

    def __init__(self, name, productName=None, configFile=None, logLevel=logging.INFO):
        # This sets up the connections to/from the hub, the logger, and the twisted reactor.
        #
        specIds = [i + 1 for i in range(1)]
        cams = ['b%i' % i for i in specIds] + ['r%i' % i for i in specIds]

        enus = ['enu_sm%i' % i for i in specIds]
        xcus = ['xcu_%s' % cam for cam in cams]
        ccds = ['ccd_%s' % cam for cam in cams]

        actorcore.ICC.ICC.__init__(self, name,
                                   productName=productName,
                                   configFile=configFile,
                                   modelNames=enus + xcus + ccds)

        self.logger.setLevel(logLevel)

        self.everConnected = False

    def requireModel(self, actorName, cmd):
        """ Make sure that we are listening for a given actor keywords. """

        if actorName not in self.models.keys():
            cmd.inform(f"text='connecting model for actor {actorName}'")
            self.addModels([actorName])

    def safeCall(self, **kwargs):
        cmd = kwargs["forUserCmd"]
        kwargs["timeLim"] = 300 if "timeLim" not in kwargs.keys() else kwargs["timeLim"]

        cmdVar = self.cmdr.call(**kwargs)

        if cmdVar.didFail:
            repStr = cmdVar.replyList[-1].keywords.canonical(delimiter=';')
            cmd.warn(repStr.replace('command failed', f'{kwargs["actor"]} {kwargs["cmdStr"].split(" ", 1)[0]} failed'))
            raise RuntimeError

        return cmdVar

    def sampleData(self, cmd, actor, cmdStr, keys, labels=None):
        doRaise = False
        keyVarDict = self.models[actor].keyVarDict
        cmdVar = self.safeCall(forUserCmd=cmd, actor=actor, cmdStr=cmdStr)

        data = []

        for i in range(self.niter):
            wait()
            cmdVar = self.safeCall(forUserCmd=cmd, actor=actor, cmdStr=cmdStr)
            data.append(newRow([list(keyVarDict[key].valueList) for key in keys]))

        data = np.array(data)
        columns = sum([[f'{actor}__{key}__{val.name}' for val in keyVarDict[key].valueList] for key in keys], [])
        columns = labels if labels is not None else columns

        return pd.DataFrame(data=data, columns=columns)

    def genSample(self, cmd, df):
        failed = []
        for col in df.columns:

            gen = cmd.inform
            if 'None' in col:
                continue
            values = df[col].astype('float64')

            if np.isnan(values.mean()):
                gen = cmd.warn
                failed.append(col)

            gen(f'{col}={round(values.mean(), 4)},{round(values.std(), 3)}')

        if failed:
            raise RuntimeError(f'{", ".join(failed)} are invalid')

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
