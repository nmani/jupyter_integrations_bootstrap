# Execute Custom Pre-Installation and Post-Installation Scripts

## ## WARNING: DO NOT COMMIT YOUR CUSTOM SCRIPTS TO THE PUBLIC REPO ##
A directory of environment or deployment specific scripts that will be executed in the order of the naming scheme. No parallel execution and will stop running if any script generates an error. If no error is created, it will move the next script. All scripts should be idempotent or as close to it as possible. Running any script twice or many times shouldn't be an issue.

# Naming convention

It must strictly follow this regex: ^\d{2}_\W+\.py$

DD_XXXX...XXX.py

01_testing.py
02_testing.py
03_testing.py