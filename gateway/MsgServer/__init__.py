__description__ = \
"""
Python class for simple message passing server
"""

__author__ = "jikuja"
__date__ = "2017-05-30"
__all__ = ["MsgServer"]

from .MsgServer import MsgServer as MsgServer
from .MsgServer import MsgHandler as MsgHandler
from .MsgServer import init_msg_server as init_msg_server
