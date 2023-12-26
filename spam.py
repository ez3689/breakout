import datetime
import threading
import time
from os import path

import zroya
from PIL import Image
from pystray import *

from hibernate import hibernate


class BasicSpam:
    def __init__(self, name: str, image_path: str):
        self.name = name
        self.image_path = image_path
        self.make_tray()

        self.spam_event = threading.Event()
        self.hibernate_event = threading.Event()
        self.hibernate_thread = None
        self.curr_notif = None

        self.start_spam()

    def spam(self):
        if not self.to_run():
            self.start_spam()
            return

        self.hibernate_thread = threading.Thread(target=self.hibernate_in, args=(1, True))

        self.spam_event.clear()
        # time.sleep(whatever) (this is for if Timers are replaced)

        while not self.spam_event.wait(5):
            self.notify()

    def start_spam(self):
        pass  # to override

    def notify(self, lines):
        status = zroya.init(
            app_name=self.name,  # todo: probably change that (make new var?)
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
        times = {0: 0, 1: 1, 2: 5, 3: 10}  # todo: make configurable (also change self.notify)

        # self.spam_timer.cancel()
        self.spam_event.set()
        self.hibernate_event.set()

        self.hibernate_thread = threading.Thread(target=self.hibernate_in, daemon=False, args=(times[action_id],))
        self.hibernate_thread.start()

        # todo: a lot more to add lol

    def hibernate_in(self, minutes=0):
        self.hibernate_event.clear()

        if self.hibernate_event.wait(minutes * 60):
            return

        self.hibernate_event.set()
        # self.spam_timer.cancel()
        self.spam_event.set()

        self.start_spam()
        hibernate()

    def calculate_next_time(self) -> int:
        """returns the amount of time until the next alarm.
        Turns out, it's USELESS LMAO"""
        pass

    def to_run(self) -> bool:  # TODO: Make this static (eventually)
        return True

    def make_tray(self):
        image = Image.open(path.abspath(path.join(path.dirname(__file__), self.image_path)))
        menu = Menu(
            MenuItem(
                self.name,
                lambda: self.hibernate_in(0),
            ),
            MenuItem(
                f"{self.name} soon",
                self.notify
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
    BasicSpam()
