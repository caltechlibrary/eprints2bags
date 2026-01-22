
# Running eprints2bag

## Challenges

eprints2bag is long in the tooth. Python version and installation setups on our servers have evolved and allow me to follow the instructions in the README.md.

~~~shell
 python -m pip install eprints2bags --user --upgrade
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try apt install
    python3-xyz, where xyz is the package you are trying to
    install.
    
    If you wish to install a non-Debian-packaged Python package,
    create a virtual environment using python3 -m venv path/to/venv.
    Then use path/to/venv/bin/python and path/to/venv/bin/pip. Make
    sure you have python3-full installed.
    
    If you wish to install a non-Debian packaged Python application,
    it may be easiest to use pipx install xyz, which will manage a
    virtual environment for you. Make sure you have pipx installed.
    
    See /usr/share/doc/python3.12/README.venv for more information.

note: If you believe this is a mistake, please contact your Python installation or OS distribution provider. You can override this, at the risk of breaking your Python installation or OS, by passing --break-system-packages.
hint: See PEP 668 for the detailed specification.
~~~

This server is running Ubuntu 24.04.3 LTS. 

## Current status

Mike has moved on and Caltech Library is migrating off of EPrints. This project is no longer maintained and is not under active development. I've updated the codemeta.json developmentStatus field to indicate it is not being developed. After the final run of bagging our EPrints repository I will archive this repository. (R.S. Doiel, 2026-01-22)

