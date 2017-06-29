"""Bar"""
class MyPyCmdMessengerMock(object):
    """Foo"""

    def __init__(self, commands):
        self.commands = commands

    def send(self, cmd, *args, **kwargs):
        pass

    def receive(self, arg_formats=None):
        pass
