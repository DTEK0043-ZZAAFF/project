from mock import MagicMock
from mock import patch
import unittest
import CmdEvents
import PyCmdMessenger
import serial

class CmdEventsTestCase(unittest.TestCase):
    def setUp(self):
        self.commands = [["foo", "s"],
                         ["bar", "?"],
                         ["baz", ""],
                         ["mixed", "s?"]]

    @patch("PyCmdMessenger.CmdMessenger")
    def testFind(self, mocked):
        mocked.commands = self.commands
        cmdEvents = CmdEvents.CmdEvents(mocked)
        self.assertTrue(cmdEvents.isMessageTypeValid("foo"))
        self.assertFalse(cmdEvents.isMessageTypeValid("notfoundatall"))

    def testCallbacktypes(self):
        with patch("serial.Serial") as MockClass:
            arduino = PyCmdMessenger.ArduinoBoard("")
            c = PyCmdMessenger.CmdMessenger(arduino, self.commands)
            cmdEvents = CmdEvents.CmdEvents(c)
            cmdEvents.addListener("foo", self.stringCallback)
            cmdEvents.addListener("bar", self.booleanCallback)
            cmdEvents.addListener("baz", self.noneCallback)
            cmdEvents.addListener("mixed", self.mixedCallback)

            MockClass.return_value.read.side_effect = list("0,asdf;")
            cmdEvents.readOnce()

            MockClass.return_value.read.side_effect = list("1,") + [chr(0x01)] + list(";")
            cmdEvents.readOnce()

            MockClass.return_value.read.side_effect = list("2;")
            cmdEvents.readOnce()

            MockClass.return_value.read.side_effect = list("3,asdf,") + [chr(0x00)] + list(";")
            cmdEvents.readOnce()

    def stringCallback(self, msg):
        self.assertEquals(msg, "asdf")

    def booleanCallback(self, msg):
        self.assertEquals(msg, True)

    def noneCallback(self, msg):
        self.assertEquals(msg, None)

    def mixedCallback(self, msg):
        self.assertEquals(len(msg), 2)
        self.assertEquals(msg[0], "asdf")
        self.assertEquals(msg[1], False)

if __name__ == '__main__':
    unittest.main()
