import datetime
import threading
from os import path

import zroya
from PIL import Image
from icecream import ic
from pystray import *

from hibernate import hibernate


class TakeBreak:
    SESSION_DURATION = 30
    BREAK_DURATION = 60
    SCHOOL_START = 8
    SCHOOL_END = 16

    def __init__(self):
        self.make_tray()

        self.spam_event = threading.Event()
        self.hibernate_event = threading.Event()
        self.hibernate_thread = None
        self.curr_notif = None

        self.spam_timer = threading.Timer(self.SESSION_DURATION * 60, self.spam)
        # self.spam_timer = threading.Timer(1, self.spam)
        # TODO: Replace with time.sleep?
        self.spam_timer.name = "og spam timer"
        self.spam_timer.start()

    def spam(self):
        if self.school_in_session() and False:  # or if this program shouldn't be running
            # RE-ENABLE AFTER BREAK
            self.spam_timer = threading.Timer(self.SESSION_DURATION * 60, self.spam)
            self.spam_timer.name = "school-started spam"
            self.spam_timer.start()
            return

        self.hibernate_thread = threading.Thread(target=self.hibernate_in, args=(1, True))
        self.hibernate_thread.name = "auto hibernate thread"
        self.hibernate_thread.start()

        ic("auto-hibernate thread started")

        self.spam_event.clear()
        # time.sleep(whatever) (this is for if Timers are replaced)

        while not self.spam_event.wait(5):  # .wait() returns True when event is set
            # todo: make sure this actually works (i think it does actually)
            self.notify()
        ic("spam event was set")

    def notify(self):
        status = zroya.init(
            app_name="Take Break",
            company_name="Company name",
            product_name="Product name",
            sub_product="Sub-product",
            version="version"
        )
        if not status:
            Exception("Initialization failed")

        template = zroya.Template(zroya.TemplateType.ImageAndText4)

        template.setFirstLine("Time to take a break!")
        template.setSecondLine("If you're done/not working, you must take a break now.")

        template.addAction("Ok")
        template.addAction("1 minute")
        template.addAction("5 minutes")

        if self.curr_notif is not None:
            pass
            # zroya.hide(self.curr_notif)

        self.curr_notif = zroya.show(template, on_action=self.on_action)

    def on_action(self, _, action_id):
        times = {0: 0, 1: 1, 2: 5, 3: 10}
        ic(action_id)

        ic("killing spam thread and auto-hibernate thread")
        self.spam_timer.cancel()
        self.spam_event.set()
        self.hibernate_event.set()  # kills the auto-hibernate thread

        self.hibernate_thread = threading.Thread(target=self.hibernate_in, daemon=False, args=(times[action_id], False))
        self.hibernate_thread.name = "self-started hibernate thread"
        self.hibernate_thread.start()

        ic("started hibernate thread")

    def hibernate_in(self, minutes=0, auto=True):
        self.hibernate_event.clear()
        ic("waiting to hibernate...")
        ic(auto)

        if self.hibernate_event.wait(minutes * 60):
            ic(f"Hibernate thread was killed")
            ic(auto)
            return

        self.hibernate_event.set()
        self.spam_timer.cancel()
        self.spam_event.set()

        self.spam_timer = threading.Timer(self.SESSION_DURATION * 60, self.spam)
        self.spam_timer.name = "post-hibernate spam timer"
        self.spam_timer.start()

        ic("ABOUT TO HIBERNATE")
        hibernate()

    def school_in_session(self) -> bool:  # TODO: Make this static (eventually)
        now = datetime.datetime.now()
        return now.weekday() < 5 and now.hour in range(self.SCHOOL_START, self.SCHOOL_END)

    def weekend(self) -> bool:
        now = datetime.datetime.now()
        return now.weekday() >= 5

    def make_tray(self):
        image = Image.open(path.abspath(path.join(path.dirname(__file__), "break-time.png")))
        menu = Menu(
            MenuItem(
                "Take break",
                lambda: self.hibernate_in(0, False),
            ),
            MenuItem(
                "Take break soon",
                self.notify
            ),
            MenuItem(
                "Print threads",
                lambda: ic(threading.enumerate())
            ),
            MenuItem(
                'Exit',
                exit_tray
            ))

        tray_icon = Icon('test', image, menu=menu)
        tray_icon.run_detached()


def exit_tray(icon, _):
    icon.stop()


if __name__ == "__main__":
    TakeBreak()
