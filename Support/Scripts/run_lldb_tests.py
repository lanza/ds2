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
import os
import sys
from subprocess import call
import argparse

def run_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", help="go faster", action="store_true")
    parser.add_argument(
        "--no-ds2-blacklists",
        help="do not use the blacklists located at ds2/Support/Testing/Blacklists/ds2",
        action="store_true",
    )
    parser.add_argument(
        "--no-upstream-blacklists",
        help="do not use the blacklists located at ds2/Support/Testing/Blacklists/upstream",
        action="store_true",
    )
    parser.add_argument(
        "--log", help="pass --remote-debug to the debugserver", action="store_true"
    )
    parser.add_argument(
        "--strace", help="run strace on the debugserver", action="store_true"
    )
    parser.add_argument(
        "--use-lldb-server", help="use lldb-server instead of ds2", action="store_true"
    )
    parser.add_argument(
        "--platform", help="run the debug server in platform mode", action="store_true"
    )
    args = parser.parse_args()
    return args


def cherry_pick_patches(lldb_path, ):
    exit(99)
    patches_path = "{}/Support/Testing/Patches".format(top)

    if "android" in PLATFORM_NAME:
        for i in ["android-search-paths.patch", "getplatform-workaround.patch"]:
            print(["patch", "-d", lldb_path, "-p1", "<", "{patches_path}/{i}"])


def get_android_compiler(arch):
    if "ARM" in arch:
        gcc_with_triple = "arm-linux-androideabi-gcc"
    elif "X86" in arch:
        gcc_with_triple = "i686-linux-android-gcc"
    else:
        print("Running LLDB tests on {} is not yet supported.")
        exit(1)
    call(["find", "/tmp/android-ndk", "-name", gcc_with_triple])


LLVM_GITHUB = "https://github.com/llvm-mirror"
UPSTREAM_LLDB_BRANCH = "release_60"
TARGET = "android"

SOURCE_DIR = call(["git", "rev-parse", "--show-toplevel"])
BUILD_DIR = os.getcwd()

HOST_PLATFORM_NAME = sys.platform


def run_sanity_checks(args):
    if HOST_PLATFORM_NAME != "linux":
        print("The lldb test suite requres a Linux host environment.")
        exit(1)
    if not os.path.exists(BUILD_DIR + "ds2"):
        print("Unable to find a ds2 binary in the current directory.")
        exit(1)
    if os.environ["PLATFORM"] == "1" and not args.platform:
        print(
            "Please use the --platform argument instead of the PLATFORM environment variable"
        )
        exit(1)
    if args.use_lldb_server and args.log:
        print(
            "Logging with lldb-server is unsupported"
        )
        exit(1)


if __name__ == "__main__":
    args = run_argument_parser()
    run_sanity_checks(args)
