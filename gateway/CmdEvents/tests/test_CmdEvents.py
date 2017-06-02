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
                         ["baz", ""]]

    @patch("PyCmdMessenger.CmdMessenger")
    def testFind(self, mocked):
        mocked.commands = self.commands
        cmdEvents = CmdEvents.CmdEvents(mocked)
        self.assertTrue(cmdEvents.isMessageTypeValid("foo"))
        self.assertFalse(cmdEvents.isMessageTypeValid("notfoundatall"))

    def testABCD(self):
        with patch("serial.Serial") as MockClass:
            arduino = PyCmdMessenger.ArduinoBoard("")
            c = PyCmdMessenger.CmdMessenger(arduino, self.commands)
            cmdEvents = CmdEvents.CmdEvents(c)

            cmdEvents.setDefaultListener(self.stringCallback)
            MockClass.return_value.read.side_effect = list("0,asdf;")
            cmdEvents.readOnce()

            cmdEvents.setDefaultListener(self.booleanCallback)
            MockClass.return_value.read.side_effect = list("1,") + [chr(0x01)] + list(";")
            cmdEvents.readOnce()

            cmdEvents.setDefaultListener(self.noneCallback)
            MockClass.return_value.read.side_effect = list("2;")
            cmdEvents.readOnce()


    def stringCallback(self, mtype, msg):
        self.assertEquals(mtype, "foo")
        self.assertEquals(len(msg), 1)
        self.assertEquals(msg[0], "asdf")

    def booleanCallback(self, mtype, msg):
        self.assertEquals(mtype, "bar")
        self.assertEquals(len(msg), 1)
        self.assertEquals(msg[0], True)

    def noneCallback(self, mtype, msg):
        self.assertEquals(mtype, "baz")
        self.assertEquals(len(msg), 0)

if __name__ == '__main__':
    unittest.main()
