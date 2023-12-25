import threading
import time

from icecream import ic

event = threading.Event()


def p():
    global event
    i = 0
    while not ic(event.wait(1)):
        i += 1
        print(i)


threading.Thread(target=p, daemon=False).start()

time.sleep(2.5)
event.set()
