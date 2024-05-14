"""
a p2p android chat
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from .p2plib import p2p_init


class AndroidChat(toga.App):

    def startup(self):
        """
        Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        main_box = toga.Box()

        send_string = p2p_init("chat", print)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box

        user_input = toga.TextInput(style=Pack(flex=1))
        main_box.add(user_input)

        def on_send(widget, **kwargs):
            send_string(user_input.value)
            user_input.value = ""

        send_button = toga.Button(
            "Send",
            on_press=on_send,
            style=Pack(padding_right=10, padding_bottom=10),
        )
        main_box.add(send_button)

        self.main_window.show()


def main():
    return AndroidChat()
