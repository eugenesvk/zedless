from contextlib import chdir, contextmanager
from glob import glob
from json import dumps
from os.path import exists
from pathlib import PurePosixPath
from subprocess import run
from tempfile import NamedTemporaryFile
from config import CONFIG

import tomlkit

import match
import match.rust

import argparse
parser = argparse.ArgumentParser(
    prog       ='Zedless Patch',
    description='Patches Zed with focus on privacy and being local-first',
    epilog     ='')
parser.add_argument('-s','--src',type=str,default="source",help="Path of the Zed's source code")
parser.add_argument('-v','--verbose',action='store_true',help="Print more info when running")
parser.add_argument('-c','--commit',action='store_true',help="Commit modified/deleted after each stage")

@contextmanager
def editTomlDocument(file):
    def callback(v):
        with open(file, "w") as f:
            tomlkit.dump(v, f)
    value = None
    with open(file, "r") as f:
        value = tomlkit.load(f)
    if value:
        yield value, callback

from pathlib      import Path
args = parser.parse_args()
import shutil
import os
dir_main = os.path.dirname(os.path.realpath(__file__))
with chdir(args.src):
    rules = []

    cratesToDelete = []
    for crate in CONFIG.bannedCrates:
        if exists(f"crates/{crate}"):
            cratesToDelete.append(crate)

    if len(cratesToDelete) > 0:
        for manifest in glob("crates/*/Cargo.toml"):
            with editTomlDocument(manifest) as (data, write):
                for crate in cratesToDelete:
                    if "dependencies" in data and crate in data["dependencies"]:
                        del data["dependencies"][crate]
                    if "dev-dependencies" in data and crate in data["dev-dependencies"]:
                        del data["dev-dependencies"][crate]
                if "features" in data:
                    for feature in data["features"]:
                        feat_filtered = list(filter(
                            lambda dep: all(
                                [
                                    not (dep.startswith(f"{crate}/")
                                    or   dep     == f"dep:{crate}"  )
                                    for crate in CONFIG.bannedCrates
                                ],
                            ), data["features"][feature]
                        ))
                        if feat_filtered != data["features"][feature]:
                            data["features"][feature] = feat_filtered
                write(data)
