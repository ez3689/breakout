import datetime
import threading
from os import path

import zroya
from PIL import Image
from icecream import ic
from plyer import notification
from pystray import *

from hibernate import hibernate


class TakeBreak:
    SESSION_DURATION = 30
    SCHOOL_START = 8
    SCHOOL_END = 16

    def __init__(self):
        self.disable_times = 0

        self.image = path.abspath(path.join(path.dirname(__file__), "break-time.png"))
        self.icon = self.make_tray()

        self.hibernate_event = threading.Event()
        self.hibernate_thread = None
        self.break_timer = None

        self.start_timer()

    def start_timer(self):
        self.break_timer = threading.Timer(self.SESSION_DURATION * 60, self.start_break)
        self.break_timer.name = "spam timer"
        self.break_timer.start()

    def start_break(self):
        if self.school_in_session:  # or if this program shouldn't be running
            self.start_timer()
            return

        self.hibernate_thread = threading.Thread(target=self.hibernate_in, args=(1, True))
        self.hibernate_thread.name = "auto hibernate thread"
        self.hibernate_thread.start()
        ic("auto-hibernate thread started")

        self.disable_times -= 1 if self.disable_times else 0

        self.notify()

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

        template = zroya.Template(zroya.TemplateType.ImageAndText2)

        template.setImage(self.image)

        template.setFirstLine("Time to take a break!")
        template.setSecondLine("If you're done/not working, you must take a break now.")

        template.addAction("Ok")
        template.addAction("1 minute")
        template.addAction("5 minutes")

        try:
            zroya.show(template, on_action=self.on_action, on_dismiss=self.on_dismiss)
        except Exception as e:
            ic(e)
            notification.notify(title="Zroya failed again", message="RUN.")

    def on_dismiss(self, _, reason):
        if not (reason or self.disable_times):
            # If user didn't dismiss toast (reason != 0) or is disabled (self.disable_times != 0)
            #  then don't show toast
            self.notify()  # todo: if toast expires, show another one (until hibernate)

    def on_action(self, _, action_id):
        times = {0: 0, 1: 1, 2: 5, 3: 10}
        ic(action_id)

        ic("killing spam thread and auto-hibernate thread")
        self.kill()

        ic("starting hibernate")
        self.hibernate_in(times[action_id], False)
        # fixme: make sure this works

    def hibernate_in(self, minutes=0, auto=True):
        self.hibernate_event.clear()
        ic("waiting to hibernate...")
        ic(auto)

        if self.hibernate_event.wait(minutes * 60):
            ic("Hibernate thread was killed")
            ic(auto)
            return

        self.kill()
        self.start_timer()

        if not (self.disable_times and auto):
            ic("ABOUT TO HIBERNATE")
            # todo: perhaps remove "or not auto" because that means that clicking will hibernate, even if disabled
            hibernate()

    def kill(self):
        """Called on action, right before hibernating

        Cancels spam before it starts

        Cancels in-progress spam
        :return:"""
        self.break_timer.cancel()
        self.hibernate_event.set()

    def disable(self, times):
        if not self.disable_times:  # == 0
            self.disable_times = times  # prevents auto hibernate two times
            # todo: make user be able to input on this
        else:
            ic(self.disable_times)

    @property
    def school_in_session(self):
        now = datetime.datetime.now()
        return not self.weekend and now.hour in range(self.SCHOOL_START, self.SCHOOL_END)

    @property
    def weekend(self):
        now = datetime.datetime.now()
        return now.weekday() >= 5

    def make_tray(self):
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
                "Disable",
                lambda: self.disable(2)
            ),
            MenuItem(
                "Print threads",
                lambda: ic(threading.enumerate())
            ),
            MenuItem(
                'Exit',
                self.exit_tray
            ))

        icon = Icon('test', Image.open(self.image), menu=menu)
        icon.run_detached()
        return icon

    def exit_tray(self):
        self.icon.stop()
        self.kill()


def get_time():
    return f"@ {datetime.datetime.now().strftime('%X')} | "


if __name__ == "__main__":
    ic.configureOutput(prefix=get_time, includeContext=True)
    TakeBreak()
