from mock import MagicMock
from mock import patch
import unittest
import CmdEvents
import PyCmdMessenger

class CmdEventsTestCase(unittest.TestCase):
    def setUp(self):
        self.commands = [["foo", "bar"],
                    ["baz", "xyzzy"]]

    @patch("PyCmdMessenger.CmdMessenger")
    def testFind(self, mocked):
        mocked.commands = self.commands
        cmdEvents = CmdEvents.CmdEvents(mocked)
        self.assertTrue(cmdEvents.isMessageTypeValid("foo"))
        self.assertFalse(cmdEvents.isMessageTypeValid("notfoundatall"))

if __name__ == '__main__':
    unittest.main()
