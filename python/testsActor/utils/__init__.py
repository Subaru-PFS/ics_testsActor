import socket
import time
from functools import partial

import numpy as np
from actorcore.QThread import QThread
from opscore.protocols import types

from pfs.utils import spectroIds

specIds = list(range(1, 5))

# Support some JHU test cryostats.
if spectroIds.getSite() == 'J':
    specIds = specIds + [8, 9]

vis = [f'b{id}' for id in specIds] + [f'r{id}' for id in specIds]
nir = [f'n{id}' for id in specIds]

enus = [f'enu_sm{id}' for id in specIds]
xcus = [f'xcu_{cam}' for cam in vis + nir]
ccds = [f'ccd_{cam}' for cam in vis]
hxs = [f'hx_{cam}' for cam in nir]

existingModels = enus + xcus + ccds + hxs


def checkDuplicate(keys):
    ''' Check if header contains any duplicates but COMMENT'''
    ignore = ['COMMENT']
    setOfElems = set()
    duplicate = []
    for key in keys:
        if key in ignore:
            continue
        elif key in setOfElems:
            duplicate.append(key)
        else:
            setOfElems.add(key)
    return duplicate


def wait():
    time.sleep(3)


def newRow(valueList):
    valueList = sum(valueList, [])
    for i, value in enumerate(valueList):
        if isinstance(value, types.Invalid):
            valueList[i] = np.nan

    return tuple(valueList)


def connectSock(host, port, timeout=1):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
    except:
        time.sleep(1)
        return False

    return True


def waitForTcpServer(host, port, timeout=60):
    start = time.time()
    port = int(port)
    while not connectSock(host, port):
        if time.time() - start > timeout:
            raise TimeoutError('tcp server %s:%d is not running' % (host, port))

    return True


def putMsg(func):
    def wrapper(self, cmd, *args, **kwargs):
        thr = QThread(self.actor, str(time.time()))
        thr.start()
        thr.putMsg(partial(func, self, cmd, *args, **kwargs))
        thr.exitASAP = True

    return wrapper


def singleShot(func):
    @putMsg
    def wrapper(self, cmd, *args, **kwargs):
        try:
            return func(self, cmd, *args, **kwargs)
        except Exception as e:
            cmd.fail('text=%s' % self.actor.strTraceback(e))

    return wrapper
