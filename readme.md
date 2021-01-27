# Snappi Tests

This repository consists of end-to-end test scripts written in [snappi](https://github.com/open-traffic-generator/snappi).

## Setup

Please make sure that the client setup meets [Python Prerequisites](#python-prerequisites).

- Clone this project, `cd` inside it.

- Install `snappi` with IxNetwork extension.

  ```sh
  python -m pip install --upgrade snappi[ixnetwork]
  ```

- Install test dependencies.

  ```sh
  python -m pip install --upgrade -r requirements.txt
  ```

- Run Tests.

  ```sh
  # provide intended API Server and port addresses
  vi tests/settings.json
  # run a test
  python -m pytest tests/raw/test_tcp_unidir_flows.py
  ```

#### Python Prerequisites

- Please make sure you have `python` and `pip` installed on your system.

  You may have to use `python3` or `absolute path to python executable` depending on Python Installation on system, instead of `python`.

  ```sh
  python -m pip --help
  ```
  
  Please see [pip installation guide](https://pip.pypa.io/en/stable/installing/), if you don't see a help message.

- It is recommended that you use a python virtual environment for development.

  ```sh
  python -m pip install --upgrade virtualenv
  # create virtual environment inside `env/` and activate it.
  python -m virtualenv env
  # on linux
  source env/bin/activate
  # on windows
  env\Scripts\activate on Windows
  ```

  **NOTE:** If you do not wish to activate virtual env, you use `env/bin/python` (or `env\scripts\python` on Windows) instead of `python`.