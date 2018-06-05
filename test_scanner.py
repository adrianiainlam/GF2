import pytest
from scanner import Symbol, Scanner
from names import Names


fulladderpath = "First report/examples/fulladder.circuit"
ripplecounterpath = "First report/examples/ripplecounter.circuit"


@pytest.fixture
def names():
    return Names()


@pytest.fixture
def scanner_fulladder(names):
    return Scanner(fulladderpath, names)


@pytest.fixture
def scanner_ripplecounter(names):
    return Scanner(ripplecounterpath, names)


@pytest.fixture
def scanner_emptyfile(names):
    return Scanner("/dev/null", names)


def test_scanner_exit_on_file_without_read_access(names):
    """
    Tests whether Scanner.__init__() exits with EXIT_FAILURE
    if it cannot read the specified file.
    """
    import os
    try:
        # create empty file
        fh = open("noreadaccess.file", "w")
        fh.close()
        # revoke read access to file
        os.chmod("noreadaccess.file", 0000)
    except OSError:  # both open() and os.chmod() can raise OSError
        # there is already no access to file
        pass

    with pytest.raises(SystemExit) as e:
        Scanner("noreadaccess.file", names)
    assert e.value.code != 0

    # cleanup
    os.remove("noreadaccess.file")


def test_scanner_emptyfile(scanner_emptyfile):
    """
    In this test, the scanner attempts to read an empty file.
    It should correctly return EOF at line 0 col 0, without raising
    any exceptions.
    """
    assert scanner_emptyfile._get_next_char() == ''
    assert scanner_emptyfile._current_char == ''
    sym = scanner_emptyfile.get_symbol()
    assert sym.symtype == scanner_emptyfile.symbol_types.EOF
    assert sym.linenum == 0
    assert sym.colnum == 0


def test_scanner_invalid_symbols(scanner_emptyfile):
    """
    In this test, a "fake" file is created consisting entirely of
    invalid symbols (and a comment). The scanner should correctly
    assign a None symbol type to all the symbols, and ignore valid
    symbols in the comment.
    """
    sc = scanner_emptyfile
    sc.filelines = ["/ * -//= +++ $%^&  !@? {}| # but not after here !@$8"]

    a = sc.get_symbol()
    print(a.symtype)
    while a.symtype != sc.symbol_types.EOF:
        print(a.symtype)
        assert a.symtype is None
        a = sc.get_symbol()


def test_scanner_get_next_char(scanner_fulladder, scanner_ripplecounter):
    """
    In this test we check whether get_next_char correctly reads
    the next char in each text file.
    """
    for sc in [scanner_fulladder, scanner_ripplecounter]:
        if sc == scanner_fulladder:
            fh = open(fulladderpath, "r")
        else:
            fh = open(ripplecounterpath, "r")

        sc._get_next_char()
        while sc._current_char != '':
            assert sc._current_char == fh.read(1)
            sc._get_next_char()
        assert fh.read(1) == ''

        fh.close()


def test_scanner_fulladder_ripplecounter(scanner_fulladder,
                                         scanner_ripplecounter):
    """
    In this test, the number of each symbol type is counted by direct
    substring searching methods. The same statistic is then tallied
    from the result of Scanner.get_symbol(), and compared to the
    direct count.
    """

    for sc in [scanner_fulladder, scanner_ripplecounter]:

        if sc == scanner_fulladder:
            fh = open(fulladderpath, "r")
        else:
            fh = open(ripplecounterpath, "r")
        content = fh.read()
        fh.close()

        import re
        # strip comments
        content = re.sub('#.*(\n|$)', '', content)
        # split by word boundary, i.e. spaces and punctuations
        content_words = re.findall(r"[\w']+", content)

        keyword_cnt = len([x for x in content_words if x in
                           ['DEVICE', 'CONNECT', 'MONITOR', 'END']])
        number_cnt = len([x for x in content_words if x.isdigit()])
        name_cnt = len(content_words) - keyword_cnt - number_cnt

        t = sc.symbol_types

        sym_cnt = {
            t.COMMA: content.count(','),
            t.DOT: content.count('.'),
            t.SEMICOLON: content.count(';'),
            t.CONNECTION_OP: content.count('->'),
            t.OPENPAREN: content.count('('),
            t.CLOSEPAREN: content.count(')'),
            t.KEYWORD: keyword_cnt,
            t.NUMBER: number_cnt,
            t.NAME_CAPS: name_cnt
            # for now we hack NAME_CAPS to store all names
        }

        a = sc.get_symbol()
        while a.symtype != t.EOF:
            if a.symtype in [t.NAME_CAPSNUM, t.NAME_ALNUM]:
                sym_cnt[t.NAME_CAPS] -= 1
            else:
                sym_cnt[a.symtype] -= 1
            a = sc.get_symbol()

        for i in sym_cnt:
            assert sym_cnt[i] == 0


def test_scanner_eof(scanner_fulladder):
    """
    In this test, the behaviour after encountering EOF is tested.
    Namely, if get_symbol() is called after EOF for an arbitrary
    number of times, the returned symbol should still be EOF, with
    no changes to line and column numbers.
    """
    sc = scanner_fulladder

    # first we read till EOF, and remember the line and column numbers
    a = sc.get_symbol()
    while a.symtype != sc.symbol_types.EOF:
        a = sc.get_symbol()
    linenum = a.linenum
    colnum = a.colnum

    # then we keep reading for an arbitrary number of times (say 10)
    for i in range(10):
        a = sc.get_symbol()
        assert a.symtype == sc.symbol_types.EOF
        assert a.linenum == linenum
        assert a.colnum == colnum


def test_scanner_get_number(scanner_emptyfile):
    """
    In this test the behaviour of _get_number() is tested by constructing
    a file with only numbers, and next by an input which is not a
    number (which we expect ValueError).
    """
    sc = scanner_emptyfile

    from random import randint
    nums = []
    for i in range(100):
        nums += [randint(0, 2147483647)]

    sc.filelines = [' '.join(str(x) for x in nums) + '\n', 'abc']
    sc._get_next_char()  # init sc to the first char

    for i in range(100):
        sc._skip_to_next_symbol()
        assert sc._get_number() == nums[i]

    with pytest.raises(ValueError):
        sc._get_number()


def test_scanner_get_name(scanner_emptyfile):
    """
    Similart to test_scanner_get_number(), but this time its names,
    i.e. alphanumeric string starting with a letter.
    """
    sc = scanner_emptyfile

    from random import randint, choice
    from string import ascii_letters, digits

    names = []
    for i in range(100):
        namelen = randint(1, 100)
        name = choice(ascii_letters)
        for j in range(namelen - 1):
            name += choice(ascii_letters + digits)
        names += [name]

    sc.filelines = [' '.join(names) + '\n', '1bc']
    sc._get_next_char()

    for i in range(100):
        sc._skip_to_next_symbol()
        assert sc._get_name() == names[i]

    with pytest.raises(ValueError):
        sc._get_name()


@pytest.mark.parametrize("filelines, linenum, colnum", [
    (['   '], 0, 3),
    (['   s'], 0, 4),
    (['   \n'], 0, 4),
    (['   \n', 's'], 1, 1),
    (['# s \n', '   \n', ' \ts'], 2, 3),
    (['s \n', '###'], 0, 1),
    (['# comment line 1\n', '# comment line 2\n', 'DEVICE\n'], 2, 1),
    (['# comment\n', '  # indented comment\n', 'DEVICE\n'], 2, 1),
    (['  # indented comment\n', '#comment\n', 'DEVICE\n'], 2, 1),
    (['  #indented\n', '   #indented\n', 'DEVICE\n'], 2, 1)
])
def test_scanner_skip_to_next_symbol(scanner_emptyfile, filelines,
                                     linenum, colnum):
    """
    Tests whether Scanner._skip_to_next_symbol() skips to the
    correct line and column.
    """
    sc = scanner_emptyfile
    sc.filelines = filelines

    sc._get_next_char()

    sc._skip_to_next_symbol()
    assert sc._current_line_num == linenum
    assert sc._current_col_num == colnum
