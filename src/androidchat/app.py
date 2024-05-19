"""
a p2p android chat
"""

import asyncio

import toga
from local_broadcast import init as p2p_init
from toga.style import Pack
from toga.style.pack import COLUMN, ROW


class AndroidChat(toga.App):

    def startup(self):
        """
        Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        self.send_string, self.p2p_deinit = None, None

        main_box = toga.Box()

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box

        self.init_button = toga.Button(
            "Init",
            on_press=self.init,
            style=Pack(padding_right=10, padding_bottom=10),
        )
        main_box.add(self.init_button)

        self.user_input = toga.TextInput(style=Pack(flex=1))
        main_box.add(self.user_input)

        send_button = toga.Button(
            "Send",
            on_press=self.on_send,
            style=Pack(padding_right=10, padding_bottom=10),
        )
        main_box.add(send_button)

        self.main_window.show()

    async def on_send(self, widget, **kwargs):
        if self.send_string is not None:
            await self.send_string(self.user_input.value)
        self.user_input.value = ""

    async def init(self, widget):
        self.send_string, self.on_exit = await p2p_init("chat", self.print)
        self.init_button.style.visibility = "hidden"
        self.init_button.style.width = 0

    async def print(self, message):
        print(message)


def main():
    return AndroidChat()
