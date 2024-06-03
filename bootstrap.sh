#!/bin/bash

# Script to quickly check for the correct verison of Python and then start running the bootstrapper script written in Python
# Warning: For Linux systems with bash only.
# Warning: Minimal error checking for edge cases.

# Move out Python version to config... TODO
set -e
MIN_MAJOR_PYVER=3
MIN_MINOR_PYVER=11
DEBUG=${DEBUG:-""}

log() {
    if [ -n "$DEBUG" ]; then
        echo "[DEBUG] $1"
    fi
}

chk_tool() {
    if ! command -v $1 &> /dev/null
    then
        echo "tool '$1' not found in PATH. Exiting.."
        exit 1
    fi
}

py_check() {
    PYTHON_BIN=$(which python)

    log "Found Python binary at: $PYTHON_BIN"
    PYCHECK_VER=$(${PYTHON_BIN} -c 'import sys; major, minor, *_ = sys.version_info; print(major, minor)')

}

run_bootstrap() {
    log "Starting bootstrapper..."
    python bootstrap.py
}

run_pre_custom() {
    log "testing"
}

chk_tool "python"
chk_tool "pip"
py_check

#run_pre_custom
run_bootstrap