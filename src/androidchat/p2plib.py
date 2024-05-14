import atexit
import socket
import threading
import time
from random import randint

import zmq
from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf


class Listener(ServiceListener):
    services = {}

    # callback is called when the elected master changes
    def __init__(self, callback=None):
        super().__init__()
        self.context = zmq.Context()
        # Create a socket for the client
        self.push_socket = self.context.socket(zmq.PUSH)
        self.sub_socket = self.context.socket(zmq.SUB)
        self.host = None
        self.callback = callback

    def update_mq_socket(self):
        host = min(
            [
                (info.parsed_addresses()[0], info.port)
                for info in self.services.values()
            ],
            default=("localhost", 8080),
        )
        self.host = f"tcp://{host[0]}:{host[1]}"
        if self.callback is not None:
            self.callback(self.host)

        self.push_socket.connect(self.host)
        self.sub_socket.connect(f"tcp://{host[0]}:{host[1]+1}")
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

    def get_socket(self):
        return self.sub_socket

    def send_string(self, msg):
        self.push_socket.send_string(msg)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        # print(f"Service {name} updated, service info: {info} ")
        self.services[name] = info
        self.update_mq_socket()

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        # print(f"Service {name} removed")
        del self.services[name]
        self.update_mq_socket()

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        # print(
        # f"Service {name} added, service info: {info} , addresses {info.parsed_addresses()}"
        # )
        self.services[name] = info
        self.update_mq_socket()


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(("10.254.254.254", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


def forward_message(base_port, transform=None):
    # Create a ZeroMQ context
    context = zmq.Context()

    # Create a REP socket
    rep_socket = context.socket(zmq.PULL)
    rep_socket.bind(f"tcp://*:{base_port}")

    # Create a PUB socket
    pub_socket = context.socket(zmq.PUB)
    pub_socket.bind(f"tcp://*:{base_port+1}")
    pub_socket.setsockopt(zmq.LINGER, 1)

    while True:
        # Wait for a message from the REP socket
        message = rep_socket.recv()
        # rep_socket.send(b"Message forwarded successfully!")
        if transform is not None:
            message = transform(message)
        # Forward the message to the PUB socket
        pub_socket.send(message)


def subscriber(get_socket, action):
    while True:
        try:
            message = get_socket().recv_string(flags=zmq.NOBLOCK)
            # Add the user input to the scrollable panel
            action(message)
        except zmq.error.Again as e:
            time.sleep(0.1)


def p2p_init(
    clan, subscriber_action, listener_callback=None, transform=None, base_port=None
):
    if base_port is None:
        base_port = randint(8000, 8999)

    zeroconf = Zeroconf()
    ws_info = ServiceInfo(
        f"_{clan}._http._tcp.local.",
        f"{get_ip()}_{base_port}._{clan}._http._tcp.local.",
        base_port,
        0,
        0,
        addresses=[get_ip()],
    )
    zeroconf.register_service(ws_info)

    def cleanup():
        zeroconf.unregister_service(ws_info)
        zeroconf.close()

    atexit.register(cleanup)

    threading.Thread(
        target=forward_message, args=(base_port, transform), daemon=True
    ).start()

    listener = Listener(listener_callback)

    def browser():
        b = ServiceBrowser(zeroconf, f"_{clan}._http._tcp.local.", listener=listener)

    threading.Thread(target=browser, daemon=True).start()

    threading.Thread(
        target=subscriber, args=(listener.get_socket, subscriber_action), daemon=True
    ).start()

    return listener.send_string
