# Script to quickly check for the correct verison of Python and then start running the bootstrapper script written in Python
# Warning: For Windows systems with PowerShell
# Warning: Minimal error checking for edge cases.

# Move out Python version to config... TODO
$MIN_MAJOR_PYVER = 3
$MIN_MINOR_PYVER = 12
$DEBUG=0

function log($msg) {
    Write-Host "[DEBUG] $msg"
}

function chk_tool($tool) {
    if (Get-Command $tool -ErrorAction SilentlyContinue){ 
        log "Found $tool in %PATH%"
    } else {
        log "Tool: $tool not found in %PATH%"
        Exit
    }
}

function py_check {
    $PYTHON_BIN = (Get-Command "python").Source

    log "Found Python binary at: $PYTHON_BIN"
    $PYCHECK_VER = (Get-Command $PYTHON_BIN \
        -c 'import sys; major, minor, *_ = sys.version_info; print(major, minor)')
    $PYCHECK_VER_MAJOR[int], $PYCHECK_VER_MINOR[int] = $PYCHECK_VER -split ' ',2
    if ($MIN_MAJOR_PYVER -ge $PYCHECK_VER_MAJOR) -and ($MIN_MINOR_PYVER -ge $PYCHECK_VER_MINOR){
        log "Python is at or above minimum version needed"
    } else {
        log "Python version is not at or above minimum required version. Exiting..."
        Exit
    }
}

function run_boostrap {
    python install.py init
}

function run_pre_custom {

}

function run_post_custom {

}


chk_tool "python"
chk_tool "pip"
pycheck

#run_pre_custom
#run_bootstrap