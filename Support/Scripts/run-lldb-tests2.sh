#!/usr/bin/env bash
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

cherry_pick_patches() {
  cd "$1"

  # Disabled and enabled tests
  local testingPath="$top/Support/Testing"

  if [[ "$platform_name" = "android" ]]; then
    # This patch is purely to improve performance on CircleCI, won't ever be upstreamed.
    patch -d "$lldb_path" -p1 < "$testingPath/Patches/android-search-paths.patch"
    patch -d "$lldb_path" -p1 < "$testingPath/Patches/getplatform-workaround.patch"
  fi

  cd "$OLDPWD"
}



if [[ "${TARGET-}" = Android-* ]]; then
  adb wait-for-device
  platform_name="android"
else
  platform_name="linux"
fi

case "${TARGET}" in
  Android-*)     cc_exe="$(get_android_compiler ${TARGET})";;
  *)             cc_exe="$(get_program_path gcc)";;
esac

if [[ "$(linux_distribution)" == "centos" ]] || $opt_build_lldb; then
  llvm_path="$build_dir/llvm"
  llvm_build="$llvm_path/build"
  lldb_path="$llvm_path/tools/lldb"
  lldb_exe="$llvm_build/bin/lldb"

  if ! $opt_fast; then
    git_clone "$REPO_BASE/llvm.git"  "$llvm_path"             "$UPSTREAM_BRANCH"
    git_clone "$REPO_BASE/lldb.git"  "$llvm_path/tools/lldb"  "$UPSTREAM_BRANCH"
    git_clone "$REPO_BASE/clang.git" "$llvm_path/tools/clang" "$UPSTREAM_BRANCH"

    cherry_pick_patches "$llvm_path/tools/lldb"

    if [ ! -e "${lldb_exe-}" ] ; then
      mkdir -p "$llvm_build"
      cd "$llvm_build"
      cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug ..
      ninja lldb
    fi
  fi
elif [ "$(linux_distribution)" == "ubuntu" ]; then
  lldb_path="$build_dir/lldb"
  lldb_exe="$(get_program_path lldb-7)"


  python_base="$build_dir/lib"
  export LD_LIBRARY_PATH=$python_base
  export PYTHONPATH="$python_base/python2.7/site-packages"

  if ! $opt_fast; then
    git_clone "$REPO_BASE/lldb.git" "$lldb_path" "$UPSTREAM_BRANCH"

    cherry_pick_patches "$lldb_path"

    # Sync lldb libs to local build dir
    rsync -a /usr/lib/x86_64-linux-gnu/       "$python_base"
    rsync -a /usr/lib/llvm-7/lib/python2.7/   "$python_base/python2.7"
    rsync -a "$python_base/liblldb-7.so"      "$python_base/liblldb.so"

    # Fix broken python lldb symlinks
    cd "$PYTHONPATH/lldb"
    for path in $( ls *.so* ); do
      new_link="$(readlink "$path" | sed 's,x86_64-linux-gnu/,,g' | sed 's,../../../../../,../../../,g')"
      rm "$path"
      ln -s "$new_link" "$path"
    done
  fi
else
  die "Testing is only supported on CentOS and Ubuntu."
fi

if [ -n "${LLDB_EXE-}" ] ; then
  lldb_exe=${LLDB_EXE}
fi

cd "$lldb_path/test"

args=(-q --executable "$lldb_exe" -u CXXFLAGS -u CFLAGS -C "$cc_exe" -v)





if [ -n "${TARGET-}" ]; then
  if [[ "${TARGET}" == "Linux-X86_64" || "${TARGET}" == "Linux-X86_64-Clang" ]]; then
    args+=("--arch=x86_64")
  elif [[ "${TARGET}" == "Linux-X86" || "${TARGET}" == "Linux-X86-Clang" || "${TARGET}" == "Android-X86" ]]; then
    args+=("--arch=i386")
  elif [[ "${TARGET}" == "Android-ARM" ]]; then
    args+=("--arch=arm")
  elif [[ "${TARGET}" == "Android-ARM64" ]]; then
    args+=("--arch=aarch64")
  fi
else
  # If this is a developer run (not running on CircleCI with a $TARGET), run all
  # tests by default.
  LLDB_TESTS="${LLDB_TESTS-all}"

  if [[ "$(uname -m)" = "x86_64" ]]; then
    args+=("--arch=x86_64")
  elif [[ "$(uname -m)" =~ "i[3-6]86" ]]; then
    args+=("--arch=i386")
  fi
fi





if $opt_strace; then
  cat >"$build_dir/ds2-strace.sh" <<EEOOFF
#!/usr/bin/env bash
exec strace -o $build_dir/ds2-strace.log $build_dir/ds2 "\$@"
EEOOFF
  chmod +x "$build_dir/ds2-strace.sh"
  server_path="$build_dir/ds2-strace.sh"
elif $opt_use_lldb_server; then
  server_path="$(get_program_path lldb-server-6.0)"
else
  server_path="$build_dir/ds2"
fi




if [[ "${PLATFORM-}" = "1" ]]; then
  if [[ "$platform_name" = "linux" ]]; then
    working_dir="$build_dir"
  elif [[ "$platform_name" = "android" ]]; then
    working_dir="/data/local/tmp"
  fi

  server_port="12345"

  args+=("--platform-name=remote-$platform_name" "--platform-url=connect://localhost:$server_port"
         "--platform-working-dir=$working_dir" "--no-multiprocess")

  server_args=("p" "--server" "--listen" "127.0.0.1:$server_port")

  if ! $opt_use_lldb_server && $opt_log; then
    server_args+=("--remote-debug" "--log-file=$working_dir/$(basename "$server_path").log")
  fi

  if [[ "$platform_name" = "linux" ]]; then
    "$server_path" "${server_args[@]}" &
    add_exit_handler kill -9 $!
  elif [[ "$platform_name" = "android" ]]; then
    debug_libdir="/tmp/debug-data/"
    mkdir -p "$debug_libdir"
    debug_libs=("/system/bin/linker" "/system/lib/libc.so" "/system/lib/libm.so" "/system/lib/libstdc++.so")
    for lib in "${debug_libs[@]}" ; do
      adb pull "$lib" "$debug_libdir"
    done
    adb push "$server_path" "$working_dir"
    adb shell "$working_dir/ds2" "${server_args[@]}" &
  fi
  sleep 3
else
  if ! $opt_use_lldb_server && $opt_log; then
    export LLDB_DEBUGSERVER_LOG_FILE="$build_dir/ds2.log"
    export LLDB_DEBUGSERVER_EXTRA_ARG_1="--remote-debug"
  fi
  export LLDB_DEBUGSERVER_PATH="$server_path"
fi

export LLDB_TEST_TIMEOUT=8m

if [ "${LLDB_TESTS-all}" != "all" ]; then
  args+=(-p "$LLDB_TESTS")
fi

# The test infrastructure (ds2 on emulator tunneled via adb talkig to lldb in a
# container) often causes hiccups and failures unrelated to ds2/lldb. We use
# --rerun-all-issues assuming to attemmpt to limit these failures.
args+=('--rerun-all-issues')

args+=(${opt_dotest_extra_args})

"${python_exe[@]}" dotest.py "${args[@]}"
