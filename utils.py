from __future__ import print_function
from threading import Thread
import time, sys
from ctypes import *
pthread = None
try:
    pthread = cdll.LoadLibrary("libpthread.dylib")
except OSError:
    pthread = cdll.LoadLibrary(util.find_library("pthread"))

class StoppableThread(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super(StoppableThread, self).__init__(group, target, name, args, kwargs)

    def terminate(self):
        pthread.pthread_cancel(self.ident)



def fix_name(name, recommend='utf-8'):
    recommend = str(recommend.replace('Encoding.', ''))
    try:
        name = name.decode(recommend)
        return name
    except:
        pass

    try:
        name = name.decode('big5')
        return name
    except:
        pass

    try:
        name = name.decode('shift-jis')
        return name
    except:
        pass

    try:
        name = name.decode('utf-16')
        return name
    except:
        pass
    return name


def time_elapse(total_sec):
    start_time = time.time()
    now_time = time.time()
    while now_time - start_time < total_sec:
        print("%.1f sec / %.1f sec" % (now_time-start_time, total_sec), end="\r")
        sys.stdout.flush()
        time.sleep(0.1)
        now_time = time.time()
    print("")
    sys.stdout.flush()
