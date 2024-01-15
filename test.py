import threading
import time

from icecream import ic

event = threading.Event()


def p():
    ic()
    ic(event.wait(60))  # it appears that event.wait behaves like a thread


threading.Thread(target=p, daemon=False).start()

threading.Timer(90, lambda: event.set()).start()
time.sleep(90)  # also test time.sleep(20)
event.set()
