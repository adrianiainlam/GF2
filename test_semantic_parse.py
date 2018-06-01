"""Test the semantic analysis components of the parse module."""


import pytest
from scanner import Symbol, Scanner
from names import Names
from parse import Parser
from devices import Devices
from network import Network
from monitors import Monitors



#All logic definition files used below are modified versions of the fulladder
#circuit which by itself parses with no errors.


#original error-less file
fulladderpath = "First report/examples/fulladder.circuit"

#following files all have one semantic error and each error is different
device_present = "bad_examples/device_present.circuit"
no_qualifier = "bad_examples/no_qualifier.circuit"
invalid_qualifier = "bad_examples/invalid_qualifier.circuit"
qualifier_present = "bad_examples/qualifier_present.circuit"
bad_device = "bad_examples/bad_device.circuit"
device_absent = "bad_examples/device_absent.circuit"
input_connected = "bad_examples/input_connected.circuit"
port_absent = "bad_examples/port_absent.circuit"
inputs_not_connected = "bad_examples/inputs_not_connected.circuit"
network_device_absent = "bad_examples/network_device_absent.circuit"
monitor_present = "bad_examples/monitor_present.circuit"
#ripplecounterpath = "bad_examples/ripplecounter.circuit"

@pytest.fixture
def names():
    """Return a new instance of the Names class."""
    return Names()


@pytest.fixture
def devices(names):
    """Return a new instance of the Devices class."""
    return Devices(names)


@pytest.fixture
def network(names, devices):
    """Return a new instance of the Network class."""
    return Network(names, devices)


@pytest.fixture
def monitors(names, devices, network):
    """Return a new instance of the Monitors class."""
    return Monitors(names, devices, network)



def test_fulladder_semantic(request, names, devices, network, monitors):
    """Testing error-less file doesn't throw errors"""
    sc = Scanner(fulladderpath, names)
    parser = Parser(names, devices, network, monitors, sc)
    assert parser.parse_network() == True



@pytest.mark.parametrize("bad_file, error_message", [
    (device_present, "SemanticError: Device has already been named"),
    (no_qualifier, "SemanticError: Device needs an inital state"),
    (invalid_qualifier, "SemanticError: Not a valid qualifier for device"),
    (qualifier_present, "SemanticError: Device does not take a qualifier"),
    (bad_device, "SemanticError: Not a valid device"),
    (device_absent, "SemanticError: Input or output device has not been named in DEVICES"),
    (input_connected, "SemanticError: Input is already in a connection"),
    (port_absent, "SemanticError: Invalid input/output port used"),
    (inputs_not_connected, "SemanticError: Not all inputs are connected"),
    (network_device_absent, "SemanticError: Input or output device has not been named in DEVICES"),
    (monitor_present, "SemanticError: Signal is monitored more than once"),
])
def test_semantic_errors(bad_file, error_message, names, devices, network, monitors, capsys):
    """Going through all the files which should throw semantic errors
    and seeing if correct error message is displayed by looking as system output
    """
    sc = Scanner(bad_file, names)
    parser = Parser(names, devices, network, monitors, sc)
    parser.parse_network()
    captured = capsys.readouterr()

    try:
        assert (error_message in captured.out)
    except AttributeError:
        assert (error_message in captured[0])
