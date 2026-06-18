#!/usr/bin/env bash
. "$(dirname "$0")/test_header"

if ! command -v zstd >/dev/null 2>&1; then
    if ! python3 -c "import zstd" >/dev/null 2>&1; then
        skip_all 'zstd not available'
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
./planet-n.tar.zst
./spaceship-1.txt.zst
./spaceship-2.txt.zst
./spaceship-3.txt.zst
./spaceship-4.txt.zst
./spaceship-5.txt.zst
./spaceship-6.txt.zst
./spaceship-7.txt.zst
./spaceship-8.txt.zst
./spaceship-9.txt.zst
__FIND__

purge
