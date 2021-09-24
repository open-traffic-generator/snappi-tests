import json
import os
import sys
import time
import dpkt


if sys.version_info[0] >= 3:
    # alias str as unicode for python3 and above
    unicode = str


# path to settings.json relative root dir
SETTINGS_FILE = "settings.json"
# path to dir containing traffic configurations relative root dir
CONFIGS_DIR = "configs"


def get_root_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_test_config_path(config_name):
    return os.path.join(
        os.path.dirname(get_root_dir()), CONFIGS_DIR, config_name
    )


def dict_items(d):
    try:
        # python 3
        return d.items()
    except Exception:
        # python 2
        return d.iteritems()


def object_dict_items(ob):
    return dict_items(ob.__dict__)


def byteify(val):
    if isinstance(val, dict):
        return {byteify(key): byteify(value) for key, value in dict_items(val)}
    elif isinstance(val, list):
        return [byteify(element) for element in val]
    # change u'string' to 'string' only for python2
    elif isinstance(val, unicode) and sys.version_info[0] == 2:
        return val.encode("utf-8")
    else:
        return val


def load_dict_from_json_file(path):
    """
    Safely load dictionary from JSON file in both python2 and python3
    """
    with open(path, "r") as fp:
        return json.load(fp, object_hook=byteify)


class Settings(object):
    """
    Singleton for global settings
    """

    def __init__(self):
        # these not be defined and are here only for documentation
        self.username = None
        self.location = None
        self.ports = []
        self.speed = "speed_1_gbps"
        self.media = None
        self.timeout_seconds = 30
        self.interval_seconds = 0.5
        self.log_level = None
        self.dynamic_stats_output = None
        self.license_servers = None
        self.ext = None
        self.promiscuous = None
        self.settings_file = SETTINGS_FILE

        self.load_from_settings_file()

    def load_from_settings_file(self):
        self.__dict__ = load_dict_from_json_file(self.get_settings_path())
        # overwrite with custom settings if it exists
        custom = os.environ.get("SETTINGS_FILE", None)
        if custom is not None and os.path.exists(custom):
            self.__dict__ = load_dict_from_json_file(custom)

    def get_settings_path(self):
        return os.path.join(get_root_dir(), self.settings_file)

    def register_pytest_command_line_options(self, parser):
        for key, val in object_dict_items(self):
            parser.addoption("--%s" % key, action="store", default=None)
        parser.addoption("--settings", action="store", default=None)

    def load_from_pytest_command_line(self, config):
        if config.getoption("settings"):
            global SETTINGS_FILE
            SETTINGS_FILE = config.getoption("settings")
            self.settings_file = SETTINGS_FILE
            self.load_from_settings_file()
        for key, val in object_dict_items(self):
            new_val = config.getoption(key)
            if new_val is not None:
                if key in ["license_servers", "ports"]:
                    # items in a list are expected to be passed in as a string
                    # where each item is separated by whitespace
                    setattr(self, key, new_val.split())
                else:
                    setattr(self, key, new_val)


# shared global settings
settings = Settings()


def get_host():
    """
    Returns api client configured according to global settings
    """
    return settings.location


def get_ext():
    """
    Returns external traffic vendor
    :return:
    """
    return settings.ext


def start_traffic(api, cfg, start_capture=True):
    """
    Applies configuration, and starts flows.
    """
    print("Setting config ...")
    check_warnings(api.set_config(cfg))
    capture_names = get_capture_port_names(cfg)
    if capture_names and start_capture:
        print("Starting capture on ports %s ..." % str(capture_names))
        cs = api.capture_state()
        cs.state = cs.START
        check_warnings(api.set_capture_state(cs))

    print("Starting transmit on all flows ...")
    ts = api.transmit_state()
    ts.state = ts.START
    check_warnings(api.set_transmit_state(ts))


def stop_traffic(api, cfg=None, stop_capture=True):
    """
    Stops flows
    """
    print("Stopping transmit on all flows ...")
    ts = api.transmit_state()
    ts.state = ts.STOP
    check_warnings(api.set_transmit_state(ts))
    if cfg is None:
        return
    capture_names = get_capture_port_names(cfg)
    if capture_names and stop_capture:
        print("Stopping capture on ports %s ..." % str(capture_names))
        cs = api.capture_state()
        cs.state = cs.STOP
        check_warnings(api.set_capture_state(cs))


def seconds_elapsed(start_seconds):
    return int(round(time.time() - start_seconds))


def timed_out(start_seconds, timeout):
    return seconds_elapsed(start_seconds) > timeout


def wait_for(
    func,
    condition_str,
    interval_seconds=settings.interval_seconds,
    timeout_seconds=settings.timeout_seconds,
):
    """
    Keeps calling the `func` until it returns true or `timeout_seconds` occurs
    every `interval_seconds`. `condition_str` should be a constant string
    implying the actual condition being tested.
    Usage
    -----
    If we wanted to poll for current seconds to be divisible by `n`, we would
    implement something similar to following:
    ```
    import time
    def wait_for_seconds(n, **kwargs):
        condition_str = 'seconds to be divisible by %d' % n
        def condition_satisfied():
            return int(time.time()) % n == 0
        poll_until(condition_satisfied, condition_str, **kwargs)
    ```
    """
    start_seconds = int(time.time())

    print("\n\nWaiting for %s ..." % condition_str)
    while True:
        res = func()
        if res:
            print("Done waiting for %s" % condition_str)
            break
        if res is None:
            raise Exception("Wait aborted for %s" % condition_str)
        if timed_out(start_seconds, timeout_seconds):
            msg = "Time out occurred while waiting for %s" % condition_str
            raise Exception(msg)

        time.sleep(interval_seconds)


def get_all_stats(api, print_output=True):
    """
    Returns all port and flow stats
    """
    print("Fetching all port stats ...")
    request = api.metrics_request()
    request.port.port_names = []
    port_results = api.get_metrics(request).port_metrics
    if port_results is None:
        port_results = []

    print("Fetching all flow stats ...")
    request = api.metrics_request()
    request.flow.flow_names = []
    flow_results = api.get_metrics(request).flow_metrics
    if flow_results is None:
        flow_results = []

    if print_output:
        print_stats(port_stats=port_results, flow_stats=flow_results)

    return port_results, flow_results


def total_frames_ok(port_results, flow_results, expected):
    port_tx = sum([p.frames_tx for p in port_results])
    port_rx = sum([p.frames_rx for p in port_results])
    flow_rx = sum([f.frames_rx for f in flow_results])

    return port_tx == port_rx == flow_rx == expected


def total_bytes_ok(port_results, flow_results, expected):
    port_tx = sum([p.bytes_tx for p in port_results])
    port_rx = sum([p.bytes_rx for p in port_results])
    flow_rx = sum([f.bytes_rx for f in flow_results])

    return port_tx == port_rx == flow_rx == expected


def print_stats(port_stats=None, flow_stats=None, clear_screen=None):
    if clear_screen is None:
        clear_screen = settings.dynamic_stats_output

    if clear_screen:
        os.system("clear")

    if port_stats is not None:
        row_format = "{:>15}" * 6
        border = "-" * (15 * 6 + 5)
        print("\nPort Stats")
        print(border)
        print(
            row_format.format(
                "Port",
                "Tx Frames",
                "Tx Bytes",
                "Rx Frames",
                "Rx Bytes",
                "Tx FPS",
            )
        )
        for stat in port_stats:
            print(
                row_format.format(
                    stat.name,
                    stat.frames_tx,
                    stat.bytes_tx,
                    stat.frames_rx,
                    stat.bytes_rx,
                    stat.frames_tx_rate,
                )
            )
        print(border)
        print("")
        print("")

    if flow_stats is not None:
        row_format = "{:>15}" * 3
        border = "-" * (15 * 3 + 5)
        print("Flow Stats")
        print(border)
        print(row_format.format("Flow", "Rx Frames", "Rx Bytes"))
        for stat in flow_stats:
            print(row_format.format(stat.name, stat.frames_rx, stat.bytes_rx))
        print(border)
        print("")
        print("")


def check_warnings(response):
    if response.warnings:
        print("Warning: %s" % str(response.warnings))


def get_all_captures(api, cfg):
    """
    Returns a dictionary where port name is the key and value is a list of
    frames where each frame is represented as a list of bytes.
    """
    cap_dict = {}
    for name in get_capture_port_names(cfg):
        print("Fetching captures from port %s" % name)
        request = api.capture_request()
        request.port_name = name
        pcap_bytes = api.get_capture(request)

        cap_dict[name] = []
        for ts, pkt in dpkt.pcap.Reader(pcap_bytes):
            if sys.version_info[0] == 2:
                cap_dict[name].append([ord(b) for b in pkt])
            else:
                cap_dict[name].append(list(pkt))

    return cap_dict


def get_capture_port_names(cfg):
    """
    Returns name of ports for which capture is enabled.
    """
    names = []
    for cap in cfg.captures:
        if cap._properties.get("port_names"):
            for name in cap.port_names:
                if name not in names:
                    names.append(name)

    return names


def mac_or_ip_to_num(mac_or_ip_addr, mac=True):
    """
    Example:
    mac_or_ip_to_num('00:0C:29:E3:53:EA')
    returns: 52242371562
    mac_or_ip_to_num('10.1.1.1', False)
    returns: 167837953
    """
    sep = ":" if mac else "."
    addr = []
    if mac:
        addr = mac_or_ip_addr.split(sep)
    else:
        addr = ["{:02x}".format(int(i)) for i in mac_or_ip_addr.split(sep)]
    return int("".join(addr), 16)


def num_to_mac_or_ip(mac_or_ip_addr, mac=True):
    """
    Example:
    num_to_mac_or_ip(52242371562)
    returns: '00:0C:29:E3:53:EA'
    num_to_mac_or_ip(167837953, False)
    returns: '10.1.1.1'
    """
    sep = ":" if mac else "."
    fmt = "{:012x}" if mac else "{:08x}"
    rng = 12 if mac else 8
    mac_or_ip = fmt.format(mac_or_ip_addr)
    addr = []
    for i in range(0, rng, 2):
        if mac:
            addr.append(mac_or_ip[i] + mac_or_ip[i + 1])
        else:
            addr.append(str(int(mac_or_ip[i] + mac_or_ip[i + 1], 16)))
    return sep.join(addr)


def mac_or_ip_addr_from_counter_pattern(start_addr, step, count, up, mac=True):
    """
    Example:
    mac_or_ip_addr_from_counter_pattern('10.1.1.1', '0.0.1.1', 2, True, False)
    returns: ['00:0C:29:E3:53:EA', '00:0C:29:E3:54:EA']
    mac_or_ip_addr_from_counter_pattern('10.1.1.1', '0.0.1.1', 2, True, False)
    teturns: ['10.1.1.1', '10.1.2.2']
    """
    addr_list = []
    for num in range(count):
        addr_list.append(start_addr)
        if up:
            start_addr = mac_or_ip_to_num(start_addr, mac) + mac_or_ip_to_num(
                step, mac
            )
        else:
            start_addr = mac_or_ip_to_num(start_addr, mac) - mac_or_ip_to_num(
                step, mac
            )
        start_addr = num_to_mac_or_ip(start_addr, mac)
    return addr_list


def flow_transmit_matches(flow_results, state):
    return len(flow_results) == all(
        [f.transmit == state for f in flow_results]
    )


def to_hex(lst):
    """
    Takes lst of data from packet capture and converts to hex
    Ex: [11,184] is converted to 0xbb8
        [0,30] is converted to 0x1e
    """
    from functools import reduce

    value = reduce(lambda x, y: hex(x) + hex(y), lst)
    value = value[0:2] + value[2:].replace("0x", "").lstrip("0")
    return value
