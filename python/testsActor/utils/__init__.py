import socket
import time
import numpy as np
from functools import partial

from actorcore.QThread import QThread
from opscore.protocols import types

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
