"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Symbol - contains attributes of a symbol
Scanner - reads definition file and translates characters into symbols.
"""

from enum import Enum
import sys


class Symbol():
    """
    Class for Symbol objects. Contains four public attributes.

    symtype: Type of the symbol, takes values in Scanner.symbol_types
    symid  : A numerical ID for the symbol; within each symtype the
             ID acts as a unique identifier
    linenum: The line number (0-indexed) at which the symbol is found
    colnum : The column number (1-indexed) at which the symbol starts

    The initialiser expects all four attributes to be present.
    """
    def __init__(self, symtype, symid, linenum, colnum):
        self.symtype = symtype
        self.symid = symid
        self.linenum = linenum
        self.colnum = colnum


class Scanner:

    """Read circuit definition file and translate the characters into symbols.

    Once supplied with the path to a valid definition file, the scanner
    translates the sequence of characters in the definition file into
    symbol types and symbol IDs that the parser can use. It also skips over
    comments and irrelevant formatting characters, such as spaces and line
    breaks.

    Parameters
    ----------
    path: path to the circuit definition file.
    names: instance of the names.Names() class.

    Public methods
    -------------
    get_symbol(self): Translates the next sequence of characters and
                      returns the symbol type and ID.

    Public (mutable) attributes
    ---------------------------
    symbol_types: An Enum containing all valid symbol types.
                  Currently the list of valid symbol types are:
                    COMMA, DOT, SEMICOLON, CONNECTION_OP, KEYWORD,
                    NUMBER, OPENPAREN, CLOSEPAREN, EOF,
                    NAME_CAPS, NAME_CAPSNUM, NAME_ALNUM
    keywords: A list of keywords
    comment_start,
    comment_end: Single-character delimiters to mark the start and end
                 of a comment. These are initialised to '#' and '\n'
                 respectively.
    filelines: A list of the lines read from the circuit file.
               '\n' are not stripped from the lines.
               Please DO NOT change the value of filelines.
    """

    def __init__(self, path, names):
        """Open specified file and initialise reserved words and IDs."""
        try:
            fh = open(path, mode='rt')
            self.filelines = fh.readlines()
            fh.close()
        except IOError:
            print("Failed to open %s for reading. Exiting." % path,
                  file=sys.stderr)
            sys.exit(1)

        self._names = names
        self.symbol_types = Enum(  # changes need to be updated in docstring
            'symbol_types',
            'COMMA DOT SEMICOLON CONNECTION_OP KEYWORD NUMBER ' +
            'OPENPAREN CLOSEPAREN EOF ' +
            'NAME_CAPS NAME_CAPSNUM NAME_ALNUM'
        )
        self.keywords = ['DEVICE', 'CONNECT', 'MONITOR', 'END']

        ## Why is this necessary? IDs will be looked up in get_symbol()
        ## anyway, and these keywords are not expected to be used
        ## frequently enough for this to bring performance enhancements.
        # keyids = self.names.lookup(self.keywords)
        # self.keywords_id = dict(zip(self.keywords, keyids))

        self.comment_start = '#'
        self.comment_end = '\n'

        self._current_char = ''
        self._current_line = ''
        self._current_line_num = 0
        self._current_col_num = 0
        self.path = path

    def _get_next_char(self):
        if len(self.filelines) == 0: # empty file
            return ''

        current_line = self.filelines[self._current_line_num]

        if self._current_col_num >= len(current_line):  # end of line

            if self._current_line_num >= len(self.filelines) - 1:  # EOF
                self._current_char = ''
            else:

                self._current_line_num += 1
                self._current_col_num = 1
                current_line = self.filelines[self._current_line_num]
                self._current_char = current_line[0]

        else:
            self._current_char = current_line[self._current_col_num]
            self._current_col_num += 1

    def _skip_to_next_symbol(self):
        isincomment = (self._current_char == self.comment_start)

        while self._current_char.isspace() or isincomment:
            self._get_next_char()
            if isincomment:
                if self._current_char in [self.comment_end, '']:
                    isincomment = False
                    self._get_next_char()
            else:
                isincomment = (self._current_char == self.comment_start)

    def get_symbol(self):
        """Return the symbol type and ID of the next sequence of characters.

        If the current character is not recognised, both symbol type and ID
        are assigned None. Note: this function is called again (recursively)
        if it encounters a comment or end of line.
        """
        if self._current_line_num == 0 and self._current_col_num == 0:
            # read the first char to start off
            self._get_next_char()

        self._skip_to_next_symbol()

        sym = Symbol(
            symtype=None, symid=None,
            linenum=self._current_line_num, colnum=self._current_col_num
        )

        if self._current_char.isalpha():  # name
            name_str = self._get_name()
            if name_str in self.keywords:
                sym.symtype = self.symbol_types.KEYWORD
            else:
                if name_str.isupper():
                    if name_str.isalpha():
                        sym.symtype = self.symbol_types.NAME_CAPS
                    else:
                        sym.symtype = self.symbol_types.NAME_CAPSNUM
                else:
                    sym.symtype = self.symbol_types.NAME_ALNUM
            sym.symid = self._names.lookup([name_str])[0]

        elif self._current_char.isdigit():  # number
            sym.symid = self._get_number()
            sym.symtype = self.symbol_types.NUMBER

        elif self._current_char == '-':  # connection operator ->
            self._get_next_char()
            if self._current_char == '>':
                sym.symtype = self.symbol_types.CONNECTION_OP
            self._get_next_char()

        elif self._current_char == ';':
            sym.symtype = self.symbol_types.SEMICOLON
            self._get_next_char()

        elif self._current_char == ',':
            sym.symtype = self.symbol_types.COMMA
            self._get_next_char()

        elif self._current_char == '.':
            sym.symtype = self.symbol_types.DOT
            self._get_next_char()

        elif self._current_char == '(':
            sym.symtype = self.symbol_types.OPENPAREN
            self._get_next_char()

        elif self._current_char == ')':
            sym.symtype = self.symbol_types.CLOSEPAREN
            self._get_next_char()

        elif self._current_char == '':
            sym.symtype = self.symbol_types.EOF

        else:
            self._get_next_char()

        return sym

    def _get_name(self):
        """
        Assumes _current_char is a letter ([A-Za-z]), and returns
        the next name in the file. "Name" is defined to be an
        alphanumeric string starting with a letter.
        If the assumption is invalid, a ValueError will be raised.
        """
        if not self._current_char.isalpha():
            raise ValueError("_get_name() encounters _current_char which " +
                             "is not a letter.")
        name = self._current_char
        self._get_next_char()
        while self._current_char.isalnum():
            name += self._current_char
            self._get_next_char()
        return name

    def _get_number(self):
        """
        Assumes _current_char is a digit, and returns the next
        non-negative integer in the file, i.e. it stops at the
        next non-digit character.
        If the assumption is invalid, a ValueError will be
        raised.
        """
        if not self._current_char.isdigit():
            raise ValueError("_get_number() encounters _current_char " +
                             "which is not a digit.")
        numstr = self._current_char
        self._get_next_char()
        while self._current_char.isdigit():
            numstr += self._current_char
            self._get_next_char()
        return int(numstr, base=10)
