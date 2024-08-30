"""
[Miscellaneous]
WindBot Misc Module
Author: Windsun
Jul 29 2024
"""

# Standard Lib Imports
import os

# Local Imports
from .game_logic import GameLoop

# Module Helper Imports
from ..moduleHelper import ModuleHelper, ModuleMetadata

mh = ModuleHelper()

__module_meta__ = ModuleMetadata(
    name="Wordle",
    desc="Windbot Wordle Module",
    extra={
        "moduleuid": "wordle",
        "version": "0.0.1",
        "author": ["Jacob Liu"],
    },
)


class Wordle:
    # Module Properties
    META: ModuleMetadata
    USER_FUNCTIONS: dict
    MNGNG_FUNCTIONS: dict
    STATIC_PATH: str

    def __init__(self):
        self.META = __module_meta__
        self.USER_FUNCTIONS = {
            "wstart": self.start,
            "wguess": self.guess,
            "wabort": self.abort,
        }
        self.MNGNG_FUNCTIONS = {}

    def wstart(self, args):
        command_args = args[0]

        if len(command_args) != 1:
            return mh.compose_txt_msg("")
