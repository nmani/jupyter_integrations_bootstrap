import os
import pytest
from typing import Any
from pathlib import Path
from install import Config, Bootstrap


@pytest.fixture
def config(tmp_path: Path, **kwargs):
    return Config(**kwargs, config_path=tmp_path)

@pytest.fixture(autouse=True)
def bstrap(config: Config):
    return Bootstrap(config)

# Mostly to make sure your pytest settings aren't off
def test_init_state(bstrap: Bootstrap):
    assert not bstrap.int_dir.exists()
    assert not bstrap.venv_dir.exists()

def test_create_dirs(bstrap: Bootstrap):
    dirs = bstrap.create_dirs()
    assert dirs == True
    assert bstrap.int_dir.exists()

def test_venv_create(bstrap: Bootstrap):
    bstrap._venv_create()
    assert bstrap.venv_dir.exists()
    assert bstrap.activate_bin.exists()

# Will mock it / test files later...
@pytest.mark.parametrize(
    "bad_program,expected",
    [
        ("import os; purposeful syntax error", False),
        ("import os; import not_a_real_module", True), # compiling != execution
        ("import os; import pytest", True)
    ]
)
def test_bstrap_compile(bstrap: Bootstrap, bad_program, expected):
    outfile =  bstrap.config.config_path / "01_testing.py"

    with open(outfile, "w") as fh:
        fh.write(bad_program)
        fh.close()
    
    assert bstrap._chk_python_compile(outfile) == expected