# snappi Tests

[![license](https://img.shields.io/badge/license-MIT-green.svg)](https://en.wikipedia.org/wiki/MIT_License)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/open-traffic-generator/snappi-tests/cicd)](https://github.com/open-traffic-generator/snappi-tests/actions/workflows/cicd.yml)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/open-traffic-generator/snappi-tests.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/open-traffic-generator/snappi-tests/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/open-traffic-generator/snappi-tests.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/open-traffic-generator/snappi-tests/context:python)

This repository consists of end-to-end test scripts written in [snappi](https://github.com/open-traffic-generator/snappi).

## Setup

Please make sure that the client setup meets [Python Prerequisites](#python-prerequisites).

>This repository is currently work-in-progress, and hence only the tests inside `tests/raw` have been tested against both [Ixia-c](https://github.com/open-traffic-generator/ixia-c) and [IxNetwork](https://www.keysight.com/in/en/products/network-test/protocol-load-test/ixnetwork.html).

- Clone this project, `cd` inside it.

- Install `snappi` (along with extensions if needed).

  ```sh
  # if no extensions are needed - e.g. for ixia-c testbed
  python -m pip install --upgrade snappi==0.7.41
  # install with ixnetwork extension - for ixnetwork testbed
  python -m pip install --upgrade "snappi[ixnetwork]==0.5.13"
  ```

- Install test dependencies.

  ```sh
  python -m pip install --upgrade -r requirements.txt
  ```

- Update `tests/settings.json`

  ```sh
  # sample for ixia-c testbed
  {
    # controller address
    "location": "https://localhost",
    "ports": [
        # traffic engine addresses 
        "localhost:5555",
        "localhost:5556"
    ],
    # since we're not using any snappi extension
    "ext": null,
    "speed": "speed_1_gbps",
    "media": null
  }
  # sample for ixnetwork testbed
  {
    # IxNetwork API Server address
    "location": "https://192.168.1.1:443",
    "ports": [
        # chassis;card;port
        "192.168.2.1;6;1",
        "192.168.2.1;6;2"
    ],
    # since we're using snappi ixnetwork extension
    "ext": "ixnetwork",
    "speed": "speed_1_gbps",
    "media": "fiber"
  }
  ```

- Run Tests.

  ```sh
  python -m pytest tests/raw/test_basic_flow_stats.py
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
