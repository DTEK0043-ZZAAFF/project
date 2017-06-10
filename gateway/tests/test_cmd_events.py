import unittest

import PyCmdMessenger
from mock import Mock
from mock import patch

from myapp import CmdEvents

class CmdEventsTestCase(unittest.TestCase):
    def setUp(self):
        self.commands = [["foo", "s"],
                         ["bar", "?"],
                         ["baz", ""],
                         ["mixed", "s?"]]

    def test_adding_callbacks(self):
        mocked_arduino = Mock()
        mocked_arduino.connected = True
        cmd_messenger = PyCmdMessenger.CmdMessenger(mocked_arduino, self.commands)
        cmd_events = CmdEvents(cmd_messenger)

        fn1 = Mock()
        fn2 = Mock()
        cmd_events.add_callback("foo", fn1)
        cmd_events.add_callback("foo", fn2)

        mocked_arduino.read.side_effect = list("0,asdf;")
        cmd_events._CmdEvents__read_once()

        # test if mocked callback functions are called
        fn1.assert_called_once_with("asdf")
        fn2.assert_called_once_with("asdf")

    def test_adding_bad_callback(self):
        mocked_arduino = Mock()
        mocked_arduino.connected = True
        cmd_messenger = PyCmdMessenger.CmdMessenger(mocked_arduino, self.commands)
        cmd_events = CmdEvents(cmd_messenger)

        fn1 = Mock()

        self.assertRaises(Exception, cmd_events.add_callback, "notfoundatall", fn1)

    def test_adding_default_callback(self):
        mocked_arduino = Mock()
        mocked_arduino.connected = True
        cmd_messenger = PyCmdMessenger.CmdMessenger(mocked_arduino, self.commands)
        cmd_events = CmdEvents(cmd_messenger)

        fn1 = Mock()
        fn2 = Mock()
        cmd_events.add_callback("foo", fn1)
        cmd_events.set_default_callback(fn2)

        mocked_arduino.read.side_effect = list("0,asdf;") + list("1,") + [chr(0x01)] + list(";")
        cmd_events._CmdEvents__read_once()
        cmd_events._CmdEvents__read_once()

        # test if mocked callback functions are called
        fn1.assert_called_once_with("asdf")
        # note totally different set of argements than regular callbacks
        fn2.assert_called_once_with("bar", [True])

    @patch("myapp.CmdEvents._CmdEvents__default_callback")
    def test_default_callback(self, mocked_function):
        mocked_arduino = Mock()
        mocked_arduino.connected = True
        cmd_messenger = PyCmdMessenger.CmdMessenger(mocked_arduino, self.commands)
        cmd_events = CmdEvents(cmd_messenger)

        fn1 = Mock()
        cmd_events.add_callback("foo", fn1)

        mocked_arduino.read.side_effect = list("0,asdf;") + list("1,") + [chr(0x01)] + list(";")
        cmd_events._CmdEvents__read_once()
        cmd_events._CmdEvents__read_once()

        # test if mocked callback functions are called
        fn1.assert_called_once_with("asdf")
        # note totally different set of argements than regular callbacks
        mocked_function.assert_called_once()
        mocked_function.assert_called_once_with("bar", [True])

    def test_find(self):
        mocked_cmd_messenger = Mock()
        mocked_cmd_messenger.commands = self.commands
        cmd_events = CmdEvents(mocked_cmd_messenger)

        # simply test if message types are found
        self.assertTrue(cmd_events._CmdEvents__message_type_valid("foo"))
        self.assertFalse(cmd_events._CmdEvents__message_type_valid("notfoundatall"))

    @patch("serial.Serial")
    def test_callbacktypes(self, mocked_class):
        arduino = PyCmdMessenger.ArduinoBoard("")
        cmd_messenger = PyCmdMessenger.CmdMessenger(arduino, self.commands)
        cmd_events = CmdEvents(cmd_messenger)
        cmd_events.add_callback("foo", self.string_callback)
        cmd_events.add_callback("bar", self.boolean_callback)
        cmd_events.add_callback("baz", self.none_callback)
        cmd_events.add_callback("mixed", self.mixed_callback)

        mocked_class.return_value.read.side_effect = list("0,asdf;")
        cmd_events._CmdEvents__read_once()

        mocked_class.return_value.read.side_effect = list("1,") + [chr(0x01)] + list(";")
        cmd_events._CmdEvents__read_once()

        mocked_class.return_value.read.side_effect = list("2;")
        cmd_events._CmdEvents__read_once()

        mocked_class.return_value.read.side_effect = list("3,asdf,") + [chr(0x00)] + list(";")
        cmd_events._CmdEvents__read_once()

    def string_callback(self, msg):
        self.assertEquals(msg, "asdf")

    def boolean_callback(self, msg):
        self.assertEquals(msg, True)

    def none_callback(self, msg):
        self.assertEquals(msg, None)

    def mixed_callback(self, msg):
        self.assertEquals(len(msg), 2)
        self.assertEquals(msg[0], "asdf")
        self.assertEquals(msg[1], False)

if __name__ == '__main__':
    unittest.main()
