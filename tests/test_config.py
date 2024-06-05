import os
import pytest
from typing import Any
from install import Config, Bootstrap

@pytest.mark.parametrize(
    "bad_config",
    [
        {'config_path': "/NOT_A_REAL_PATH_I_HOPE"},
        {'config_path': "/"},
        {'config_path': "C:\\"},
        {'python': 2.12 },
        {'python': "212" },
        {'python': "3.11" }, # not min python version
        {'python': 3.11 }, # not min python version
        {'python': .313 },
        {'overwrite': None },
        {'overwrite': .313 },
        {'overwrite': "falssse" },
        {'overwrite': "trueeee" },
        {'env_prefix': " integ rations " },
        {'env_prefix': "!i@lnt-\'egrations" },
    ]
)
def test_config_badparams(bad_config):
    with pytest.raises(AssertionError):
        Config(bootstrap_yaml=None, **bad_config)

@pytest.mark.parametrize(
    "in_obj,expected",
    [
    ({'python': 3.33}, {'python': '3.33'}),
    ({'overwrite': True}, {'overwrite': True}),
    ({'custom_something': True}, {'custom_vars' : {'custom_something': True}}),
    ]
)
def test_config_override_fn(in_obj: dict[str, Any], expected: Any):
    config = Config()
    config._override_vars(in_obj)
    for k, v in in_obj.items():
        if 'custom_vars' in expected:
            assert config.__dict__['custom_vars'] == expected['custom_vars']
        else:
            assert config.__dict__[k] == expected[k]

@pytest.mark.parametrize(
    "in_env,expected",
    [
        ('PYTHON', '3.33'),
        ('OVERWRITE', True),
    ]
)
def test_env_override(in_env, expected):
    os.environ[f"INTEGRATIONS_{in_env}"] = str(expected)
    blah = Config()
    assert getattr(blah, str(in_env).lower()) == expected