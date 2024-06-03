# Juypter Integration Bootstrapper

## Overiew
This bootstrapper's logic checks to see if the environment is ready for Integrations. For use in primarily restricted environments where software cannot be set up manually or require multiple levels of approvals.

Checks (in the following order):
1) Making sure the correct minimum version of Python is installed on the system.
2) Config files are installed in the correct location location or create them as needed.
3) Run pre-bootstrap custom scripts (company specific)
4) Run the bootstrap script (should be a single pip install) #TODO
5) Run post-bootstrap custom scripts (company specific)
5) Finish 

The bootstrap script is idempotent. It can be run multiple times and result in the same outcome. When configuration already exist, it will not overwrite the current values.

NOTE: NOTHING SHOULD RUN AS ROOT EVER

## Config (Default Values)
--------

```yaml
overwrite: False # Default Value
env_prefix: INTEGRATIONS # Default, case-sensitive prefix used to add/override all integrations variables.
config_path: /home/user/.config # Default WIN: %USERPROFILE%, LINUX: $HOME
config_dir: integrations # Default: "integrations" ie- /home/user/.config/integrations
bootap_yaml: config.yml # Default location of bootstrap configuration parameters file
custom_yaml: custom.yml # Default location of custom site-specific parameters that will override and add to existing config parameters
min_python: 3.12 # minimum Python version required
```

The folder integrations_config_template is an example config directory. 

This folder will be documented more completely as we go, but the recommedation is copy this to a location at your org and update this folder to work in your org. Putting in customized options for setup, and which reports will be installed. 

PROTIP: Store the config in a private or internal repo to track changes and use that in an install script depending on your bootstrap. 

You should only need to edit config.yml. If you wish to override or include any additional variables that are site-specific, use the override_config.yml file.

### Configuration Overriding

1) ENV VARIABLES (ie - INTEGRATIONS_OVERWRITE=TRUE)
2) 

## Bootstrapping Steps

    2a) Very that pip install works via proxy
    2a) Verify keyring access from keyring module
    2a) If it exists already, fail and give instructions on how to overwrite it.
    2b) If the doesn't exist, make it with a default configuration
3) Run the custom department specific pre-provisioning scripts
    3a) You can either (1) maintain a fork() or tthis repo and rebase against main or (2) submodule the directory against an internal repo
4) Run

## Bootstraps
-----------
There will be installs for various platforms that read the config and install the integrations as needed. 

Only Linux and Windows are supported.

## Custom Executie PRE / Post Scripts

All pre/post scripts run as processes. You should pass configuration parameters to them