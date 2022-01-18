"""
PyTest configuration script
"""

def pytest_addoption(parser):
    parser.addoption(
        "--ws-config-file",
        dest="ws_config_file",
        action="append",
        default=[],
        help="Workspace configuration file",
    )

def pytest_generate_tests(metafunc):
    if "ws_config_file" in metafunc.fixturenames:
        metafunc.parametrize("ws_config_file", metafunc.config.getoption("ws_config_file"))