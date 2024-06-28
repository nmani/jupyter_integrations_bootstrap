#!/bin/env python

import os
import sys
import argparse
import logging as lg
import yaml
import subprocess
import keyring
import venv
import py_compile
from shutil import rmtree
from getpass import getuser, getpass
from dataclasses import dataclass, field
from importlib.util import find_spec
from pathlib import Path, PosixPath, WindowsPath
from typing import Any

__VERSION__ :str = '0.01a'
lg.basicConfig(level=lg.DEBUG)

#TODO: refactor assert to f() w/ custom Exception here
#TODO: lg.error -> sys.exit() logic to something better
#TODO: add a bunch more logging for sanity reasons

@dataclass
class Config:
    overwrite: str | bool = False
    interactive: str | bool = False
    env_prefix: str = "INTEGRATIONS"
    keyring: str = 'integrations'
    config_path: str | Path = Path.home() 
    config_dir: str = 'integrations'
    bootstrap_yaml: str | Path = Path("config.yml")
    custom_path: str | Path = Path("custom_exec")
    custom_yaml: str | Path =  custom_path / "custom.yml"
    custom_vars: dict[str, Any] = field(default_factory=dict)
    python: str | float = f'{sys.version_info.major}.{sys.version_info.minor}'
    #repos: list[dict[str, dict[str, Any]]] = None

    def _chk_python_ver(self) -> None:
        lg.info("Validating the Python version...")
        curr_major, curr_minor, *_ = sys.version_info
        ver_chk = [int(x) for x in str(self.python).split('.')]
        assert len(ver_chk) == 2, f"Python version didn't parse to two ints. Value: {self.python}"
        assert ver_chk[0] == 3, f"Must be Python 3 at a minimum for the bootstrap script"
        assert ver_chk[1] >= 12, f"Must be Python 3.12 at a minimum for the bootstrap script"
        assert (curr_major == ver_chk[0]) or (curr_minor <= ver_chk[1]), f"Installed Python {curr_major}.{curr_minor} does not match desired Python: {ver_chk[0]}.{ver_chk[1]}"
        
    def _chk_config_dir(self) -> None:
        lg.info("Validating the config directory...")

        self.config_path = Path(self.config_path) if isinstance(self.config_path, str) else self.config_path

        if not isinstance(self.overwrite, bool):
            overwrite_val = str(self.overwrite).lower().strip()
            assert overwrite_val in ['true', 'false'], f"Overwrite config value can only be True or False"
            if overwrite_val == "true":
                self.overwrite = True
            elif overwrite_val == "false":
                self.overwrite = False

        assert isinstance(self.overwrite, bool), f"Overwrite config value is not bool True/False"

        # TODO: CHECK IF IT'S HOME
        config_path = self.config_path
        integrations_path: Path = self.config_path / self.config_dir
        assert config_path.exists(), f"Config Path: {config_path} does not exist..."
        assert config_path.is_dir(), f"Config Path: {config_path} is not a directory"
        assert not integrations_path.exists() or (integrations_path.exists() and self.overwrite == True), \
               f"Integrations directory {integrations_path} already exists and overwrite is not enabled."

        # Only consistent way to test if a directory / file is writable in Windows
        if isinstance(config_path, WindowsPath):
            tmpfile = config_path / "tmpfile"
            try:
                with open(tmpfile, "w") as fh:
                    fh.write("testing")
                    fh.close()
            except PermissionError as err:
                lg.error(f"Permission Error for {config_path}: {err}")
                sys.exit(1)
            except IOError as err:
                lg.error(f"Non Permission-related IOError: {err}")
                sys.exit(1)
            finally:
                if tmpfile.exists():
                    tmpfile.unlink()
        elif isinstance(config_path, PosixPath):
            assert os.access(config_path, os.W_OK), f"Config path: {config_path} is not writable"
        else:
            lg.error(f"Not a WindowsPath/PosixPath: {type(config_path)}")
            sys.exit(1)
            
        assert config_path.owner() == getuser(), f"The config_path owner: {config_path.owner} does not match current owner: {os.getuid}"
        assert config_path.absolute() != config_path.absolute().anchor, f"config_path: {config_path} is a OS root directory..."
        
    def _load_yaml(self, fl: str | Path) -> dict[str, Any]:
        try:
            with open(fl) as fh:
                output = yaml.safe_load(fh)
        except yaml.YAMLError as err:
            lg.error(err)
        except Exception as err:
            lg.error(err)
        return output

    def _stdbool(self, input: Any) -> bool:
        true_names = ["true", "yes", "y", "1"]
        false_names = ["false", "no", "n", "0"]
        input_cmp = str(input).lower().strip()

        if input_cmp in true_names:
            return True
        elif input_cmp in false_names:
            return False
        else:
            lg.error(f"{input_cmp} doesn't map to a boolean value")
            raise AssertionError

    def _override_vars(self, in_obj: dict[str, Any]) -> dict[str, Any]:
        for k, new_val in in_obj.items():
            if k in self.__dict__:
                curr_val = self.__dict__[k]
                if curr_val == new_val:
                    continue
                lg.info(f"Overriding standard key [{k}] from: [{curr_val}] to new value: [{new_val}]")
                if self.__annotations__[k] == str | bool:
                    bool_val = self._stdbool(new_val)
                    self.__dict__.update({k:bool_val})
                else:
                    self.__dict__.update({k:type(curr_val)(new_val)})
            else:
                lg.info(f"New key: [{k}], Value: [{new_val}] not found standard config options. Adding it to custom config options.")
                self.custom_vars.update({k:new_val})

    def _fin_conf(self) -> None:
        # Common bootstrap YAML file
        if not isinstance(self.bootstrap_yaml, Path):
            self.bootstrap_yaml = Path(self.custom_yaml)

        if self.bootstrap_yaml.exists():
            common_yaml = self._load_yaml(self.bootstrap_yaml) # Common Config
            if common_yaml:
                self._override_vars(common_yaml)
    
        # Site-specific config overrides
        if not isinstance(self.custom_yaml, Path):
            self.custom_yaml = Path(self.custom_yaml)

        if self.custom_yaml.exists():
            custom_env = self._load_yaml(self.custom_yaml)
            if custom_env:
                self._override_vars(custom_env)
        
        assert str(self.env_prefix).isalnum(), f"env_prefix should be alphanumeric with no spaces or special characters" 

        # ENV overrides
        relevant_env: dict[str, Any] = {}
        for k, v in os.environ.items():
            prefix_length = len(self.env_prefix)
            if k[:prefix_length] == self.env_prefix.upper():  # Case sensitive
                if k[prefix_length+1:] == k[len(self.env_prefix)+1:].upper(): # EVERYTHING after env_prefix should also be upper
                    lg.debug(f"Found matching ENV [{k}] with value: [{v}]. Adding/overriding existing value")
                    lg.debug(f"Extracted relevant env to: {k[prefix_length+1:].lower()}")
                    relevant_env.update({k[prefix_length+1:].lower():v})

        self._override_vars(relevant_env)

    def __post_init__(self) -> None:
        self._fin_conf()
        self._chk_python_ver()
        self._chk_config_dir()

# BOOTSTRAP STEPS
# * Check for PROXY vars and nuke them if internal only environment
# * Run the pre-bootstrap scripts (if needed)
# * Write the config files in their locations
# * Set up .venv
# * Install all the relevant/useful packages
# * Set up Juypterlab start up scripts
# * Run post installation scripts

class Bootstrap:
    def __init__(self, config :Config) -> None:
        self.config = config
        self.int_dir :Path = self.config.config_path / self.config.config_dir
        self.venv_dir :Path = self.int_dir / '.venv'
        self.activate_bin = self.venv_dir / 'bin' / self._activate_bin()

    def _chk_python_compile(self, pyscript: str | Path) -> bool:
        try:
            py_compile.compile(pyscript, invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP, doraise=True)
        except py_compile.PyCompileError as err:
            lg.error(f"Compiling Error: {err}")
            return False
        except Exception as err:
            return False
        else:
            return True

    #TODO: Allowing running across all files without failing for validation
    def extract_scripts(self, script_dir: str | Path) -> list:
        bad_compile, good_compile = [], []
        scripts_dir = Path(script_dir) if isinstance(script_dir, str) else script_dir
        if not scripts_dir.exists() or scripts_dir.is_file():
            lg.error(f"Directory: {scripts_dir} is not found")
            raise FileNotFoundError

        for fl in os.listdir(scripts_dir):
            fh = Path(fl)
            if fh.suffix.lower() == '.py': # Run only Python files
                lg.info(f"Checking file: {fh} in {scripts_dir}")
                if self._chk_python_compile(fh):
                    good_compile.append(fh)
                else:
                    lg.error(f"File: {fh} failed to compile...")
                    bad_compile.append(fh)
                    
        if len(bad_compile) > 0:
            lg.error(f"Due to syntax error in some Python scripts. Failing...")
            raise SyntaxError
        
        return sorted(good_compile)

    # Dangerous logic but there's no easy way around it to run internal specifics without a divergent codebases
    # Do not blindly trust things.  Validate the scripts you're running!
    # Shell = True makes it even more insecure.
    #subprocess.run([sys.executable, "-m", "pip", "install", pkg],

    def py_exec(self, args: str | Path | list, sh: bool = True) -> int:
        cmd = [sys.executable]
        if isinstance(args, (str, Path)):
            cmd += [Path(args).absolute()]
        elif isinstance(args, list):
            cmd += args
        else:
            lg.error(f"Unexpected type for args: {type(args)} - {args}")
            raise TypeError

        try:
            output: subprocess.CompletedProcess = \
                subprocess.run(
                    cmd,
                    shell=sh,
                    capture_output=True
                )
        except Exception as err:
            lg.error(f"Error: {err}")
            raise
        else:
            if output.returncode != 0:
                lg.error(f"Python command generated error code {output.returncode}")
            lg.debug(f"Args: {output.args}")
            lg.debug(f"STDOUT: {output.stdout}")
            lg.debug(f"STDERR: {output.args}")
        return output.returncode

    #TODO: Add logic for checking if it's update 
    def create_dirs(self) -> bool:
        if self.int_dir.exists() and self.config.overwrite:
            lg.warning(f"Integrations directory: {self.int_dir} exists and overwrite config is True. Deleting the old directory.")
            try:
                rmtree(self.int_dir)
            except Exception as err:
                lg.error(err)
                raise Exception
        elif self.int_dir.exists() and not self.config.overwrite:
            lg.warning(f"Integrations directory: {self.int_dir} exists and overwrite is False. Running an update instead...")
            # logic for update here?
        else:
            try:
                self.int_dir.mkdir(
                    parents=True,
                    exist_ok=False)
            except Exception as err:
                lg.error(f"Failed to create directory due to: {err}")
                raise
            return True
    
    def getset_kpwd(self) -> str:
        pwd = keyring.get_password(self.config.keyring, getuser)
        
        if not pwd:
            lg.error("Null or no password was provided")
            if self.config.interactive == False:
                pwd = getpass("Input your password")
                keyring.set_password(self.config.keyring, getuser(), pwd)

            else:
                lg.error("No password provided and interactive mode.")
                sys.exit(1)
    
    def _activate_bin(self, platform :str = sys.platform) -> str:
        return "Activate.ps1" if platform.startswith("win32") else 'activate'

    def _pre_bootstrap(self) -> None:
        pass

    def _post_bootstrap(self) -> None:
        pass

    def _chk_pip(self, pkgs :str | list[str] = None, install :bool = False) -> bool:
        pkgs = [pkgs] if isinstance(pkgs, str) else pkgs
        pkgs.insert(0, 'pip') # Always check for pip module first and constantly out of paranoia

        for pkg in pkgs:
            spec = find_spec(pkg)
            if spec is None:
                lg.warning(f"Required package: {pkg} is not installed. Will attempt installation...")
                if install:
                    lg.debug(f"Attempting to install Python package: {pkg}")
                    self.pip_install(pkg)
                else:
                    lg.error(f"Manually install the following packages: {pkgs}")
                    raise ImportError
            return False


    def _setup_venv(self) -> None:
        self.venv_dir / "bin"

        if not self.venv_dir.exists():
            self._venv_create()

    def _venv_create(self) -> None:
        lg.info(f"Creating venv in folder: {self.venv_dir}")
        try:
            venv.create(
                Path(self.venv_dir),
                system_site_packages=False,
                clear=True,
                with_pip=True,
                prompt=None,
                upgrade_deps=False
            )
        except Exception as err:
            lg.error(f"{err}")
            raise

    def _write_template(self) -> None:
        pass


def main(args):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Integrations Bootstrapper',
        description='CLI tool to set up prereqs for integrations in Windows / Linux',
        epilog=f'Version {__VERSION__}'
    )

    subparsers = parser.add_subparsers(title="subcommands", description="commands")
    init_parser = subparsers.add_parser("init", help="Initialize bootstrapper")
    init_parser.add_argument('--dry-run', action='store_true', help="Validate config and access checks first...")
    init_parser.add_argument('--remake', action='store_true', help="Remake configuration from scratch")

    config_parser = subparsers.add_parser("config", help="Check configuration files")
    config_parser.add_argument('-c', '--chk_conf', action='store_true', help="Checks configuration files and outputs the config object")

    update_parser = subparsers.add_parser("update", help="Update Current Environment")
    update_parser.add_argument('-u', '--update', action='store_true', help="Updates current config (if appliciable) and reruns the bootstrapper.")

    custom_runner = subparsers.add_parser("custom", help="Run custom code and logic")
    update_parser.add_argument('-l', '--list', action='store_true', help="List custom scripts available")
    args = parser.parse_args()