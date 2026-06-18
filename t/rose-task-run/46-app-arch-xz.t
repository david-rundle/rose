#!/usr/bin/env bash
. "$(dirname "$0")/test_header"

if ! command -v xz >/dev/null 2>&1; then
    if ! python3 -c "import lzma" >/dev/null 2>&1; then
        skip_all 'xz/lzma not available'
    fi
fi

tests 3

export CYLC_CONF_PATH=
export ROSE_CONF_PATH=

get_reg
run_pass "-install" \
    cylc install \
        "/" \
        --workflow-name="" \
        --no-run-name

run_pass "-play" \
    cylc play \
        "" \
        --abort-if-any-task-fails \
        --host=localhost \
        --no-detach \
        --debug

TEST_KEY="-archive-find"
(cd "/foo/20130101/hello/worlds" && find . -type f) | LANG=C sort >".out" 
file_cmp ".out" ".out" <<'__FIND__'
./planet-n.tar.xz
./spaceship-1.txt.xz
./spaceship-2.txt.xz
./spaceship-3.txt.xz
./spaceship-4.txt.xz
./spaceship-5.txt.xz
./spaceship-6.txt.xz
./spaceship-7.txt.xz
./spaceship-8.txt.xz
./spaceship-9.txt.xz
__FIND__

purge
