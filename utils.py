from __future__ import print_function
from threading import Thread, Event
import time, sys


class StoppableThread(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super(StoppableThread, self).__init__(group, target, name, args, kwargs)
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


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
