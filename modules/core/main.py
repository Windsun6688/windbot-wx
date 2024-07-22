# WindBot Core Functions Module
# May 2024

# Standard Lib Imports

# Third Party Imports

# Module Helper Imports
from ..moduleHelper import ModuleHelper, ModuleMetadata

mh = ModuleHelper()

__module_meta__ = ModuleMetadata(
    name =  "Core",
    desc =  "Windbot Basic Functions",
    extra = {
        "moduleuid": "core",
        "version": "0.0.1",
        "author": ["Windsun"],
    }
)

class Core(object):
    # Module Properties
    META: ModuleMetadata
    USER_FUNCTIONS: dict
    STATIC_PATH: str

    def __init__(self):
        super(Core, self).__init__()
        self.META = __module_meta__
        self.USER_FUNCTIONS = {
            "hi": self.say_hi,
        }
        self.MNGNG_FUNCTIONS = {
            "hi_mng": self.say_hi,
        }
        self.STATIC_PATH = mh.compose_static_path("core")

    def say_hi(self, args):
        reply = mh.compose_txt_msg("THIS SHOULD BE SENT")
        return reply

