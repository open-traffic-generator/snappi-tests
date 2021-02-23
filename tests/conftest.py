import pytest
import snappi
import utils as utl


def pytest_exception_interact(node, call, report):
    # end all pytests on first exception that is encountered
    pytest.exit(call.excinfo.traceback[0])


def pytest_addoption(parser):
    # called before running tests to register command line options for pytest
    utl.settings.register_pytest_command_line_options(parser)


def pytest_configure(config):
    # callled before running (configuring) tests to load global settings with
    # values provided over command line
    utl.settings.load_from_pytest_command_line(config)


@pytest.fixture
def settings():
    # global settings
    return utl.settings


@pytest.fixture(scope='session')
def api():
    # handle to make API calls
    api = snappi.api(host=utl.settings.api_server, ext=utl.settings.ext)
    yield api
    if getattr(api, 'assistant', None) is not None:
        api.assistant.Session.remove()

@pytest.fixture
def b2b_raw_config():
    return utl.get_b2b_raw_config()


@pytest.fixture
def utils():
    return utl


@pytest.fixture(scope='session')
def tx_addr():
    """Returns a transmit port
    """
    return utl.settings.ports[0]


@pytest.fixture(scope='session')
def rx_addr():
    """Returns a receive port
    """
    return utl.settings.ports[1]

