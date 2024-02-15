import datetime
import threading
from os import path
from tkinter import simpledialog

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
        self.can_disable = True
        self.disabled_in_school = True

        self.image = path.abspath(path.join(path.dirname(__file__), "break-time.png"))
        self.icon = self.make_tray()

        self.hibernate_event = threading.Event()
        self.break_event = threading.Event()

        self.start_break()

    def start_break(self):
        self.break_event.clear()
        was_set = self.break_event.wait(self.SESSION_DURATION * 60)

        if was_set or (self.school_in_session and self.disabled_in_school):  # or if it shouldn't be running
            threading.Thread(target=self.start_break).start()
            return

        self.disable_times -= 1 if self.disable_times else 0

        notification.notify(title="Hibernating soon!", message="Like in literally a minute")

        self.hibernate_in(1, True)

    def hibernate_in(self, minutes=0, auto=True):
        self.hibernate_event.clear()
        ic("waiting to hibernate...")
        ic(auto)

        if self.hibernate_event.wait(minutes * 60):
            ic("Hibernate thread was killed")
            ic(auto)
            return

        self.kill()

        if not (self.disable_times and auto):
            ic("ABOUT TO HIBERNATE")
            # todo: perhaps remove "or not auto" because that means that clicking will hibernate, even if disabled
            self.can_disable = True
            threading.Thread(target=self.start_break).start()  # todo: create function that runs (only) this
            hibernate()

    def kill(self):
        self.break_event.set()
        self.hibernate_event.set()

    def disable(self):
        if not self.disable_times and self.can_disable:  # == 0
            times = simpledialog.askinteger("Choose break length",
                                            "Enter the number of half hours you want to disable",
                                            initialvalue=1, minvalue=1, maxvalue=6)
            if times is not None:
                self.disable_times = times
                self.can_disable = False

    def toggle_disabled_in_school(self, _, item):
        self.disabled_in_school = not item.checked

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
                "Disable",
                self.disable
            ),
            MenuItem(
                "Disabled during school",
                self.toggle_disabled_in_school,
                checked=lambda item: self.disabled_in_school
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
