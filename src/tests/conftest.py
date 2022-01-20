"""
PyTest configuration script
"""

def pytest_addoption(parser):
    """
    Register argparse-style options.
    """
    parser.addoption(
        "--ws-config-file",
        dest="ws_config_file",
        action="append",
        default=[],
        help="Workspace configuration file",
    )

def pytest_generate_tests(metafunc):
    """
    Defines the custom parametrization schema for each test. It is called each
    time a test is collected.
    """
    if "ws_config_file" in metafunc.fixturenames:
        metafunc.parametrize("ws_config_file", metafunc.config.getoption("ws_config_file"))
