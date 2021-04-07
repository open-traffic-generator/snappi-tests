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
def b2b_raw_config(api):
    """
    back to back raw config
    """
    config = api.config()

    tx, rx = (
        config.ports
        .port(name='tx', location=utl.settings.ports[0])
        .port(name='rx', location=utl.settings.ports[1])
    )

    l1 = config.layer1.layer1()[0]
    l1.name = 'l1'
    l1.port_names = [rx.name, tx.name]
    l1.media = utl.settings.media
    l1.speed = utl.settings.speed

    flow = config.flows.flow(name='f1')[-1]
    flow.tx_rx.port.tx_name = tx.name
    flow.tx_rx.port.rx_name = rx.name

    # this will allow us to take over ports that may already be in use
    config.options.port_options.location_preemption = True

    cap = config.captures.capture(name='c1')[-1]
    cap.port_names = [rx.name]
    cap.format = cap.PCAP

    return config


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


@pytest.fixture
def bgp_convergence_config(api, utils):
    return utils.bgp_convergence_config(api, utils)
