import pytest
from scanner import Symbol, Scanner
from names import Names
from parse import Parser


fulladderpath = "First report/examples/fulladder.circuit"
ripplecounterpath = "First report/examples/ripplecounter.circuit"


@pytest.fixture
def names():
    return Names()


@pytest.fixture
def parser_fulladder(names):
    sc = Scanner(fulladderpath, names)
    return Parser(names, None, None, None, sc)


@pytest.fixture
def parser_ripplecounter(names):
    sc = Scanner(ripplecounterpath, names)
    return Parser(names, None, None, None, sc)


@pytest.fixture
def parser_emptyfile(names):
    sc = Scanner("/dev/null", names)
    return Parser(names, None, None, None, sc)


# The main testing strategy for now would be to inject different
# values of _current_sym to the parser to test various functions.
# After all these are done, a final test will be done on actual
# complete input files.

# Convenient function for SPlitting a multiline string into the
# "filelines" format used by Scanner, keeping '\n' intact.
def sp(x):
    return [x + '\n' for x in multilinestr.split('\n')][1:]


@pytest.mark.parametrize("filelines, correctness", [
    ([""], False),
    (["DEVICE"], False),
    (["CONNECT"], False),
    (["MONITOR"], False),
    (["END"], False),
    (["AND"], True),
    (["ABCDESFDSFDSFCWDSCX"], True),
    (["and"], False),
    (["And"], False),
    (["aND"], False),
    (["AND1"], False),
    (["And1"], False),
    ([","], False),
    ([";"], False),
    (["32768"], False),
    (["-"], False)
])
def test_parse_device_type(parser_emptyfile, filelines, correctness):
    p = parser_emptyfile
    sc = p._scanner
    sc.filelines = filelines

    p._current_sym = sc.get_symbol()

    assert p._parse_device_type() == correctness


@pytest.mark.parametrize("filelines, correctness", [
    ([""], False),
    (["DEVICE"], False),
    (["CONNECT"], False),
    (["MONITOR"], False),
    (["END"], False),
    (["ABCDESFDSFDSFCWDSCX"], True),
    (["AND"], True),  # This (and the next 3) should throw semantic errors,
    (["and"], True),  # but are still syntactically correct.
    (["And"], True),
    (["aND"], True),
    (["AND1"], True),
    (["And1"], True),
    ([","], False),
    ([";"], False),
    (["32768"], False),
    (["_"], False)
])
def test_parse_device_name(parser_emptyfile, filelines, correctness):
    p = parser_emptyfile
    sc = p._scanner
    sc.filelines = filelines

    assert p._parse_device_name() == correctness


@pytest.mark.parametrize("filelines, correctness", [
    ([""], False),
    (["DEVICE"], False),
    (["CONNECT"], False),
    (["MONITOR"], False),
    (["END"], False),
    (["ABCDESFDSFDSFCWDSCX"], True),
    (["AND"], True),  # This (and the next 3) should throw semantic errors,
    (["and"], True),  # but are still syntactically correct.
    (["And"], True),
    (["aND"], True),
    (["AND1"], True),
    (["And1"], True),
    (["and1(1)"], True),
    (["and1(0)"], True),  # again, semantic error but not syntax
    (["and1(-1)"], False),  # minus sign not allowed in grammar
    (["and1()"], False),
    (["and1(1,"], False),
    (["and1 (1)"], True),
    (["and1\n", "(\n", "1\n", "\n", ")"], True),
    ([","], False),
    ([";"], False),
    (["32768"], False),
    (["_"], False)
])
def test_parse_device(parser_emptyfile, filelines, correctness):
    p = parser_emptyfile
    sc = p._scanner
    sc.filelines = filelines

    assert p._parse_device() == correctness


@pytest.mark.parametrize("filelines, correctness", [
    (["AND and1;"], True),
    (["AND a1, a2;"], True),
    (["AND a1(1), a2;"], True),
    (["AND a1(100);"], True),
    (sp("""
AND a1(10000000000000),



a2
(

2



)

;
"""
        ), True),
    (["AND , a2;"], False),
    (["AND ;"], False),
    (["AND OR o1;"], False),
    (["AND"], False),
    (["AND a1,;"], False),
    (["AND a1(1 2);"], False),
    (["AND CONNECT a -> b.I1;"], False),
    (["CONNECT a -> b.I1;"], False),
    (["and1;"], False)
])
def test_parse_device_def(parser_emptyfile, filelines, correctness):
    p = parser_emptyfile
    sc = p._scanner
    sc.filelines = filelines

    p._current_sym = sc.get_symbol()

    assert p._parse_device_def() == correctness


@pytest.mark.parametrize("filelines, correctness", [
    (sp("""
DEVICE
    XOR x1, x2; ### comment
    AND a1(1), a2(2), a3(3#), a4(4);
), a4(4);
    # comment
CONNECT
"""
        ), True),
    (["DEVICE XOR x1,x2;AND a1(1),a2(2);CONNECT"], True),
    (sp("""
DEVICE
CONNECT
"""
        ), True),
    (["device"], False),  # lowercase keyword
    (["DEVICE xor"], False),  # lowercase type name
    (sp("""
DEVICE
    XOR x1, x2;
"""
        ), False),  # EOF reached before next keyword
    (sp("""
DEVICE
    AND a1,     # <- Syntax error here
    XOR x2;
CONNECT
"""
        ), False),  # comma should be semicolon
    (sp("""
DEVICE
    AND a1, a2;
    OR o1
    CLOCK ck(2);
CONNECT
"""
        ), False),  # missing semicolon in OR line
    (sp("""
DEVICE
    AND
CONNECT
"""
        ), False),  # got keyword when expecting name
    (sp("""
DEVICE
    AND
    OR o1;
CONNECT
"""
        ), False),  # should be interpreted as missing COMMA or SEMICOLON
                    # between OR and o1
    # EOF at different unexpected locations:
    (sp("""
DEVICE
    AND
"""
        ), False),
    (sp("""
DEVICE
    AND a1,
"""
        ), False),
    (sp("""
DEVICE
    AND a1(
"""
        ), False),
    (sp("""
DEVICE
    AND a1(1
"""
        ), False),
    (sp("""
DEVICE
    AND a1(1)
"""
        ), False),
    # commas and semicolons at unexpected locations:
    (sp("""
DEVICE
    AND a1(, a2;
CONNECT
"""
        ), False),
    (sp("""
DEVICE
    AND a1; a2;
CONNECT
"""
        ), False),
    (sp("""
DEVICE
    AND a1,(1), a2;
CONNECT
"""
        ), False),
    (sp("""
DEVICE
    AND a1(;
CONNECT
"""
        ), False),
    # invalid symbols
    (sp("""
DEVICE
    AND a_;
CONNECT
"""
        ), False),
    (sp("""
DEVICE
    AND a($);
CONNECT
"""
        ), False)
])
def test_parse_device_list(parser_emptyfile, filelines, correctness):
    p = parser_emptyfile
    sc = p._scanner
    sc.filelines = filelines

    assert p._parse_device_list() == correctness


@pytest.mark.parametrize("filelines, correctness", [
    (["and1"], True),
    (["dff1.Q"], True),
    (["DFF.QBAR"], True),
    (["DFF1.Q"], True),
    (sp("""
DFF

.
Q
"""
        ), True),
    (["and1.1"], False),
    (["and1.I1"], False),
    (["and1.N"], True),  # syntax correct, but semantic error
    (["dff..QBAR"], False),
    (["MONITOR.Q"], False),
    (["1.Q"], False),
    ([""], False),
    (["dff."], False),
    (["dff.;"], False),
    ([";"], False),
    (["$"], False)
])
def test_parse_output(parser_emptyfile, filelines, correctness):
    p = parser_emptyfile
    sc = p._scanner
    sc.filelines = filelines

    p._current_sym = sc.get_symbol()
    assert p._parse_output() == correctness


@pytest.mark.parametrize("filelines, correctness", [
    (["and1"], False),
    (["dff1.DATA"], True),
    (["DFF.CLOCK"], True),
    (["DFF1.Q"], True),
    (sp("""
DFF

.
Q
"""
        ), True),  # syntax correct, but semantic error
    (["and1.I1"], True),
    (["and1.1"], False),
    (["and1.N"], True),  # syntax correct, but semantic error
    (["dff..QBAR"], False),
    (["MONITOR.RESET"], False),
    (["1.Q"], False),
    ([""], False),
    (["dff."], False),
    (["dff.;"], False),
    ([";"], False),
    (["$.I1"], False),
    (["$"], False)
])
def test_parse_input(parser_emptyfile, filelines, correctness):
    p = parser_emptyfile
    sc = p._scanner
    sc.filelines = filelines

    assert p._parse_input() == correctness


@pytest.mark.parametrize("filelines, correctness", [
    (["a1 -> a2.I1;"], True),
    (["d1.Q -> d2.CLOCK;"], True),
    (["a1 -> a2.I1, a2.I2;"], True),
    (["d1.Q -> d2.CLOCK, d3.RESET, d4.DATA, a1.I3;"], True),
    (["a1 -> a2;"], False),
    (["a1"], False),
    (["a1;"], False),
    (["a1 ->"], False),
    (["a1 -> ;"], False),
    (["a1 --> a2.I1;"], False),
    (["a1 -> a2.I1, a3;"], False),
    (["a1 -"], False),
    (["a1 -;"], False),
    (["a1 - a2.I1;"], False),
    (["a1 a2.I1;"], False),
    (["a1 = a2.I1;"], False),
    (["a1 -> a2"], False),
    (["a1 -> a2."], False),
    (["a1 -> a2.;"], False),
    (["a1 -> a2.I1 a3.I1;"], False),
    (["a2.I1 -> a1;"], False),
    (["a1 -> a2.I1,"], False),
    (["a1 -> a2.I1,;"], False),
    (["d1."], False),
    ([""], False)
])
def test_parse_connection(parser_emptyfile, filelines, correctness):
    p = parser_emptyfile
    sc = p._scanner
    sc.filelines = filelines

    p._current_sym = sc.get_symbol()
    assert p._parse_connection() == correctness


@pytest.mark.parametrize("filelines, correctness", [
    (sp("""
CONNECT
  a1 -> a2.I2;
MONITOR
"""
        ), True),
    (["CONNECT MONITOR"], True),
    (sp("""
CONNECT
  a1 -> a2.I2, a3.I1;
  d.QBAR -> a1.I2;
  d.Q -> a2.I1;
  a3 -> a1.I1;
MONITOR
"""
        ), True),
    (["CONNECT"], False),
    (["MONITOR MONITOR"], False),
    (["CONNECT a1 -> a2.I1;"], False),
    (sp("""
CONNECT
  a1 -> a2.I1;
  a2 -> a1.I1;
"""
        ), False),
    (["CONNECT a1 ->"], False)
])
def test_parse_connect_list(parser_emptyfile, filelines, correctness):
    p = parser_emptyfile
    sc = p._scanner
    sc.filelines = filelines

    p._current_sym = sc.get_symbol()
    assert p._parse_connect_list() == correctness


# Parser._parse_monitor_list() only parses until no more comma, and
# does NOT parse for END keyword, but will perform EOF checks.
@pytest.mark.parametrize("filelines, correctness", [
    (["MONITOR a1 END"], True),
    (["MONITOR a1, a2 END"], True),
    (["MONITOR dff.Q END"], True),
    (["MONITOR a1, dff.Q, a2, dff2.QBAR END"], True),
    (["MONITOR a1, DEVICE, a2 END"], False),
    (["MONITOR a1, END"], False),
    (["MONITOR a1"], False),
    (["MONITOR END"], False),
    (["MONITOR DEVICE END"], False),
    ([""], False),
    (["MONITOR a1, dff. END"], False),
    (["MONITOR a1, a2"], False),
    (["CONNECT a1 -> a2.I1;"], False),
    (["MONITOR"], False)
])
def test_parse_monitor_list(parser_emptyfile, filelines, correctness):
    p = parser_emptyfile
    sc = p._scanner
    sc.filelines = filelines

    p._current_sym = sc.get_symbol()
    assert p._parse_monitor_list() == correctness


# final syntax correctness tests
@pytest.mark.parametrize("parser_str, correctness", [
    ('parser_fulladder', True),
    ('parser_ripplecounter', True),
    ('parser_emptyfile', False)
])
def test_final_syntax_correctness(parser_str, correctness, request):
    p = request.getfixturevalue(parser_str)
    assert p.parse_network() == correctness
