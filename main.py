import datetime
import threading
from os import path
from tkinter import simpledialog

import pynput
from PIL import Image
from icecream import ic
from plyer import notification
from pystray import *

from hibernate import hibernate


class TakeBreak:
    SESSION_DURATION = 30
    BREAK_LENGTH = 60
    SCHOOL_START = 8
    SCHOOL_END = 16

    def __init__(self):
        self.disable_times = 0
        self.can_disable = True
        self.disabled_in_school = True

        self.image = path.abspath(path.join(path.dirname(__file__), "break-time.png"))
        self.icon = self.make_tray()

        self.hibernate_event = threading.Event()
        self.auto_hibernate_event = threading.Event()
        self.break_event = threading.Event()
        self.input_event = threading.Event()

        self.mouse_listener = pynput.mouse.Listener(
            on_click=self.on_input, on_scroll=self.on_input
        )
        self.keyboard_listener = pynput.keyboard.Listener(
            on_press=self.on_input, on_release=self.on_input
        )

        self.mouse_listener.start()
        self.keyboard_listener.start()

        self.start_break()

    def start_break(self):
        self.break_event.clear()
        was_set = self.break_event.wait(self.SESSION_DURATION * 60)

        if was_set or (self.school_in_session and self.disabled_in_school):  # or if it shouldn't be running
            threading.Thread(target=self.start_break).start()
            return

        self.disable_times -= 1 if self.disable_times else 0

        self.begin_break(1, True)

    def begin_break(self, minutes, auto=False):
        notification.notify(title="Break starting soon!", message=f"In {minutes} minute(s)")

        event = self.auto_hibernate_event if auto else self.hibernate_event

        if not auto:
            self.auto_hibernate_event.set()

        event.clear()
        if event.wait(minutes * 60):
            return

        self.kill()

        notification.notify(title="Break in progress!", message="Don't move a muscle.")
        threading.Timer(5, self.wait).start()

    def wait(self):
        self.input_event.clear()
        if self.input_event.wait(self.BREAK_LENGTH) and not self.disable_times:
            hibernate()
        else:
            notification.notify(title="Break over!", message="Back to work!")

        self.can_disable = True
        threading.Thread(target=self.start_break).start()

    def on_input(self, *_):
        self.input_event.set()

    def kill(self):
        self.hibernate_event.set()
        self.auto_hibernate_event.set()
        self.break_event.set()
        self.input_event.set()

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
                "Take break in...",
                Menu(
                    *[
                        MenuItem(
                            f"{m} minutes",
                            threading.Thread(target=self.begin_break, args=[m]).start
                        ) for m in [0, 1, 3]
                    ]
                ),
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
        self.mouse_listener.stop()
        self.keyboard_listener.stop()


def get_time():
    return f"@ {datetime.datetime.now().strftime('%X')} | "


if __name__ == "__main__":
    ic.configureOutput(prefix=get_time, includeContext=True)
    TakeBreak()
