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
run_pass "${TEST_KEY_BASE}-install" \
    cylc install \
        "${TEST_SOURCE_DIR}/${TEST_KEY_BASE}" \
        --workflow-name="${FLOW}" \
        --no-run-name

run_pass "${TEST_KEY_BASE}-play" \
    cylc play \
        "${FLOW}" \
        --abort-if-any-task-fails \
        --host=localhost \
        --no-detach \
        --debug

TEST_KEY="${TEST_KEY_BASE}-archive-find"
(cd "${FLOW_RUN_DIR}/foo/20130101/hello/worlds" && find . -type f) | LANG=C sort >"${TEST_KEY}.out"
file_cmp "${TEST_KEY}.out" "${TEST_KEY}.out" <<'__FIND__'
./planet-n.tar.zst
./spaceships/spaceship-1.txt.zst
./spaceships/spaceship-2.txt.zst
./spaceships/spaceship-3.txt.zst
./spaceships/spaceship-4.txt.zst
./spaceships/spaceship-5.txt.zst
./spaceships/spaceship-6.txt.zst
./spaceships/spaceship-7.txt.zst
./spaceships/spaceship-8.txt.zst
./spaceships/spaceship-9.txt.zst
__FIND__

purge
