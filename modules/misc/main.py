"""
[Miscellaneous]
WindBot Misc Module
Author: Windsun
Jul 29 2024
"""

# Standard Lib Imports
import random
import os
from datetime import datetime

# Third Party Imports
from pytz import timezone

# Local Imports
from .gosenchoyen.generator import genImage

# Module Helper Imports
from ..moduleHelper import ModuleHelper, ModuleMetadata

mh = ModuleHelper()

__module_meta__ = ModuleMetadata(
    name="Misc",
    desc="Windbot Misc & Meme Module",
    extra={
        "moduleuid": "misc",
        "version": "0.0.1",
        "author": ["Windsun"],
    },
)


class Misc(object):
    # Module Properties
    META: ModuleMetadata
    USER_FUNCTIONS: dict
    MNGNG_FUNCTIONS: dict
    STATIC_PATH: str

    def __init__(self):
        self.META = __module_meta__
        self.USER_FUNCTIONS = {
            "parrot": self.party_parrot,
            "gosen": self.gen_gosen,
            "friday": self.friday_in_cali,
        }
        self.MNGNG_FUNCTIONS = {}
        self.STATIC_PATH = mh.compose_static_path("misc")
        self._init_static()

    def _init_static(self):
        self.PARROT_PATH = os.path.join(self.STATIC_PATH, "parrot")
        self.HD_PARROT = os.path.join(self.PARROT_PATH, "hd")
        self.FRIDAY_VID = os.path.join(self.STATIC_PATH, "friday.mp4")
        self.GOSEN_PIC = os.path.join(self.STATIC_PATH, "5000.jpeg")

    # Randomly Pick and Send a Party Parrot gif
    def party_parrot(self, args):
        func_data = args[0]

        # Read User Input
        if len(func_data) > 0:
            keyword = func_data[0]
        else:
            keyword = None

        # Lowres
        if keyword == "l":
            parrot_path = self.PARROT_PATH
        # HD
        elif keyword == None:
            parrot_path = self.HD_PARROT
        # Others
        else:
            reply = f"没有该参数：{keyword}"
            return mh.compose_txt_msg(reply)

        # Choose a Parrot
        chosen_parrot = random.choice(os.listdir(parrot_path))
        # If the folder "hd" is randomly chosen
        while chosen_parrot == "hd":
            chosen_parrot = random.choice(os.listdir(parrot_path))

        chosen_parrot_path = os.path.join(parrot_path, chosen_parrot)

        reply = f"你的鹦鹉是：\n{chosen_parrot.replace('.gif', '')}"

        return [mh.compose_attach_msg(chosen_parrot_path), mh.compose_txt_msg(reply)]

    # Check if Today is Friday in California
    def friday_in_cali(self, args):
        cali_tz = timezone("America/Los_Angeles")

        # If Today is Friday in California
        if int(datetime.now(cali_tz).strftime("%w")) == 5:
            reply = "Today is Friday in California.\nSHOOT!"
            return [mh.compose_attach_msg(self.FRIDAY_VID), mh.compose_txt_msg(reply)]

        # If today is not Friday in California
        else:
            reply = "Today is not Friday in California."
            return mh.compose_txt_msg(reply)

    # Generate GosenchoyenHoshiii Picture
    def gen_gosen(self, args):
        func_data = args[0]

        # User did not provide input, default message
        if len(func_data) == 0:
            first_keyword = "5000兆円"
            second_keyword = "欲しい!"
        # User provided more than two msg
        elif len(func_data) != 2:
            reply = f"gosen只能接受上下两句哦。您输入了{len(func_data)}句！"
            return mh.compose_txt_msg(reply)
        # Reasonable Input
        else:
            first_keyword = func_data[0]
            second_keyword = func_data[1]

        # Generate Gosen Image
        genImage(word_a=first_keyword, word_b=second_keyword).save(self.GOSEN_PIC)

        return mh.compose_attach_msg(self.GOSEN_PIC)
