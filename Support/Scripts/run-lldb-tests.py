#!/usr/bin/env python3
##
## Copyright (c) 2014-present, Facebook, Inc.
## All rights reserved.
##
## This source code is licensed under the University of Illinois/NCSA Open
## Source License found in the LICENSE file in the root directory of this
## source tree. An additional grant of patent rights can be found in the
## PATENTS file in the same directory.
##

# This script runs the full lldb test suite found in the LLDB repository
# against ds2. It requires a few hacks in the testing infra to disable
# broken unit tests.

from enum import Enum, auto
import argparse
import os
import subprocess
import sys
from functools import lru_cache


def parse_arguments():
    a = argparse.ArgumentParser()
    a.add_argument("--fast", action="store_true")
    a.add_argument("--no-ds2-blacklists", action="store_true")
    a.add_argument("--no-upstream-blacklists", action="store_true")
    a.add_argument("--log", action="store_true")
    a.add_argument("--pudb", action="store_true")
    a.add_argument("--strace", action="store_true")
    a.add_argument("--use-lldb-server", action="store_true")
    a.add_argument("--build-lldb", action="store_true")
    a.add_argument("--dotest-extra-args")

    return a.parse_args()




class Blacklist:
    class Type(enum):
        DS2 = auto()
        UPSTREAM = auto()

        def __repr__(self):
            return "f{self.name}".lower()

    class Condition(enum):
        ARM = auto()
        ARM64 = auto()
        X86 = auto()
        X86_64 = auto()
        ANDROID = auto()
        CENTOS = auto()
        DARWIN = auto()
        WINDOWS = auto()
        LLVM = auto()
        PLATFORM = auto()
        NON_DEBUGSERVER = auto()
        GENERAL = auto()
        INVALID = auto()

        def __repr__(self):
            return "f{self.name}".lower()

    ALL = [
        Blacklist(Type.DS2, [Condition.ANDROID, Condition.ARM64]),
        Blacklist(Type.DS2, [Condition.ANDROID]),
        Blacklist(Type.DS2, [Condition.ANDROID, Condition.INVALID]),
        Blacklist(Type.DS2, [Condition.CENTOS]),
        Blacklist(Type.DS2, [Condition.GENERAL]),
        Blacklist(Type.DS2, [Condition.LLVM]),
        Blacklist(Type.DS2, [Condition.PLATFORM]),
        Blacklist(Type.DS2, [Condition.X86]),
        Blacklist(Type.DS2, [Condition.X86, Condition.PLATFORM]),
    ]

    def __init__(self, type: Blacklist.Type, conditions: list[blacklist.Condition]) -> None:
        self.type = type
        self.conditions = conditions

    def get_path(self) -> str:
        return os.path.join(self.blacklist_path, self.type, "-".join(map(str,self.conditions)))


def select_blacklists() -> list[Blacklist]:
    # if android
    # if centos
    # if llvm
    # if platform
    # if x86
    return []


class RunLLDBTests:

    LLVM_MIRROR_URL = "https://github.com/llvm-mirror"
    LLVM_BRANCH = "release_70"
    NDK_ROOT = "/tmp/android-ndk"

    def get_blacklist_conditions_for_target(self) -> list[Blacklist.Condition]:
        conditions = []

        coditions.append(Blacklist.Condition.GENERAL)
        coditions.append(Blacklist.Condition.INVALID)
        coditions.append(Blacklist.Condition.NON_DEBUGSERVER)

        if self.target_is_android():
            conditions.append(Blacklist.Condition.ANDROID)
        elif self.target_is_linux():
            conditions.append(Blacklist.Condition.LINUX)
        elif self.target_is_windows():
            conditions.append(Blacklist.Condition.WINDOWS)

        if self.target_is_arm64():
            conditions.append(Blacklist.Condition.ARM64)
        elif self.target_is_arm():
            conditions.append(Blacklist.Condition.ARM)
        elif self.target_is_x86_64():
            conditions.append(Blacklist.Condition.X86_64)
        elif self.target_is_x86():
            conditions.append(Blacklist.Condition.X86)

        if self.is_platform_mode():
            conditions.append(Blacklist.Condition.PLATFORM)

        return conditions


    def select_blacklists(conditions: list[Blacklist.Condition]) -> list[str]:

    def __init__(self, args):
        self.args = args
        self.DS2_ROOT = suprocess.run(
            "git rev-parse --show-toplevel", shell=True
        ).stdout
        self.BUILD_DIR = os.curdir

    def get_android_compiler(self) -> str:
        if "android" not in self.target.lower():
            print(f"ERROR: should not be looking for android compiler for target {self.target}")
            sys.exit(1)
        if "arm64" in self.target.lower():
            cc_name = "aarch64-linux-android-gcc"
        elif "arm" in self.target.lower():
            cc_name = "arm-linux-androideabi-gcc"
        elif "x86" in self.target.lower():
            cc_name = "i686-linux-android-gcc"
        else:
            print(f"Unknown target {self.target}")
            sys.exit(1)

        for root, dirs, files in os.walk(self.NDK_ROOT):
            if cc_name in files:
                return os.path.join(root, name)

        print(f"Can't find Androic compiler for {self.target}")
        sys.exit(1)


    def apply_patches(self):
        ## adjust paths
        patches = ["android-search-paths.patch", "getplatform-workaround.patch"]
        for patch in patches:
            subprocess.run(["patch", "-d", lldb_path, "-p1", "<", patch])

    @lru_cache()
    def host_is_linux(self) -> bool:
        return "linux" in sys.platform

    @lru_cache()
    def host_is_darwin(self) -> bool:
        return "darwin" in sys.platform

    @lru_cache()
    def target_is_linux(self) -> bool:
        return "linux" in self.target.lower()

    @lru_cache()
    def target_is_android(self) -> bool:
        return "android" in self.target.lower()

    def run_sanity_checks(args: argparse.Namespace):
        if not host_is_linux():
            print("The lldb test suite requires a Linux host environment.")
            return 1
        if not os.path.exists(os.path.join(ds2_root, "ds2")):
            print("Unable to find a ds2 binary in the current directory.")
            return 1
        if args.use_lldb_server and args.log:
            print("Logging with lldb-server is unsupported")
            return 1

    def set_python_executable(self):
        self.python_executable = ["python2.7"]
        if self.args.pudb:
            self.python_executable.append("-m")
            self.python_executable.append("pudb")

    def set_target():
        if self.args.target is not None:
            self.target = self.args.target
        elif os.environ["TARGET"] is not None:
            self.target = os.environ["TARGET"]
        elif os.environ["CIRCLE_JOB"] is not None:
            self.target = os.environ["CIRCLE_JOB"]
        else:
            print("ERROR: No target")
            sys.exit(1)


def main() -> int:

    args = parse_arguments()
    rlt = RunLLDBTests(args)

    rlt.run_sanity_checks()
    rlt.set_python_executable()
    rlt.set_target()


    if "Android" in target:
        ##adb wait-for-device
        platform_name = "android"
        cc_executable = get_android_compiler(target)
    else:
        platform_name = "linux"
        cc_executable = get_linux_compiler()

    if host_is_centos():
        pass
    elif host_is_ubuntu():
        pass


if __name__ == "__main__":
    sys.exit(main())
