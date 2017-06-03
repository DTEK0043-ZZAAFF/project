from mock import MagicMock
from mock import Mock
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

    def testAddingCallbacks(self):
        mockedArduino = Mock()
        mockedArduino.connected = True
        c = PyCmdMessenger.CmdMessenger(mockedArduino, self.commands)
        cmdEvents = CmdEvents.CmdEvents(c)

        fn1 = Mock()
        fn2 = Mock()
        cmdEvents.addListener("foo", fn1)
        cmdEvents.addListener("foo", fn2)

        mockedArduino.read.side_effect = list("0,asdf;")
        cmdEvents.readOnce()

        # test if mocked callback functions are called
        fn1.assert_called_once_with("asdf")
        fn2.assert_called_once_with("asdf")

    def testAddingBadCallback(self):
        mockedArduino = Mock()
        mockedArduino.connected = True
        c = PyCmdMessenger.CmdMessenger(mockedArduino, self.commands)
        cmdEvents = CmdEvents.CmdEvents(c)

        fn1 = Mock()

        self.assertRaises(Exception, cmdEvents.addListener, "notfoundatall", fn1)

    def testAddingDefaultCallback(self):
        mockedArduino = Mock()
        mockedArduino.connected = True
        c = PyCmdMessenger.CmdMessenger(mockedArduino, self.commands)
        cmdEvents = CmdEvents.CmdEvents(c)

        fn1 = Mock()
        fn2 = Mock()
        cmdEvents.addListener("foo", fn1)
        cmdEvents.setDefaultListener(fn2)

        mockedArduino.read.side_effect = list("0,asdf;") + list("1,") + [chr(0x01)] + list(";")
        cmdEvents.readOnce()
        cmdEvents.readOnce()

        # test if mocked callback functions are called
        fn1.assert_called_once_with("asdf")
        # note totally different set of argements than regular callbacks
        fn2.assert_called_once_with("bar", [True])

    @patch("CmdEvents.CmdEvents.default_listener")
    def testDefaultCallback(self, mockedFunction):
        mockedArduino = Mock()
        mockedArduino.connected = True
        c = PyCmdMessenger.CmdMessenger(mockedArduino, self.commands)
        cmdEvents = CmdEvents.CmdEvents(c)

        fn1 = Mock()
        cmdEvents.addListener("foo", fn1)

        mockedArduino.read.side_effect = list("0,asdf;") + list("1,") + [chr(0x01)] + list(";")
        cmdEvents.readOnce()
        cmdEvents.readOnce()

        # test if mocked callback functions are called
        fn1.assert_called_once_with("asdf")
        # note totally different set of argements than regular callbacks
        mockedFunction.assert_called_once
        mockedFunction.assert_called_once_with("bar", [True])

    def testFind(self):
        mockedCmdMessenger = Mock()
        mockedCmdMessenger.commands = self.commands
        cmdEvents = CmdEvents.CmdEvents(mockedCmdMessenger)

        # simply test if message types are found
        self.assertTrue(cmdEvents.isMessageTypeValid("foo"))
        self.assertFalse(cmdEvents.isMessageTypeValid("notfoundatall"))

    @patch("serial.Serial")
    def testCallbacktypes(self, MockClass):
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
