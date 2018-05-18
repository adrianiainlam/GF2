"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Scanner - reads definition file and translates characters into symbols.
"""

from enum import Enum
import sys

DEBUG = sys.stderr


class Symbol():
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

        self.names = names
        self.symbol_types = Enum(
            'symbol_types',
            'COMMA DOT SEMICOLON CONNECTION_OP KEYWORD NUMBER ' +
            'NAME OPENPAREN CLOSEPAREN EOF'
        )
        self.keywords = ['DEVICE', 'CONNECT', 'MONITOR', 'END']

        keyids = self.names.lookup(self.keywords)
        self.keywords_id = dict(zip(self.keywords, keyids))

        self.comment_start = '#'
        self.comment_end = '\n'

        self.current_char = ''
        self.current_line = ''
        self.current_line_num = 0
        self.current_col_num = 0

    def get_next_char(self):
        current_line = self.filelines[self.current_line_num]

        if self.current_col_num >= len(current_line):  # end of line

            if self.current_line_num >= len(self.filelines) - 1:  # EOF
                self.current_char = ''
            else:

                self.current_line_num += 1
                self.current_col_num = 1
                current_line = self.filelines[self.current_line_num]
                self.current_char = current_line[0]

        else:
            self.current_char = current_line[self.current_col_num]
            self.current_col_num += 1

    def skip_to_next_symbol(self):
        isincomment = (self.current_char == self.comment_start)

        while self.current_char.isspace() or isincomment:
            self.get_next_char()
            if isincomment:
                if self.current_char == self.comment_end:
                    isincomment = False
                    self.get_next_char()
            else:
                isincomment = (self.current_char == self.comment_start)

    def get_symbol(self):
        """Return the symbol type and ID of the next sequence of characters.

        If the current character is not recognised, both symbol type and ID
        are assigned None. Note: this function is called again (recursively)
        if it encounters a comment or end of line.
        """
        if self.current_line_num == 0 and self.current_col_num == 0:
            # read the first char to start off
            self.get_next_char()

        self.skip_to_next_symbol()

        sym = Symbol(
            symtype=None, symid=None,
            linenum=self.current_line_num, colnum=self.current_col_num
        )

        if self.current_char.isalpha():  # name
            name_str = self.get_name()
            print(name_str, file=DEBUG)
            if name_str in self.keywords:
                sym.symtype = self.symbol_types.KEYWORD
            else:
                sym.symtype = self.symbol_types.NAME
            sym.symid = self.names.lookup([name_str])[0]

        elif self.current_char.isdigit():  # number
            sym.symid = self.get_number()
            sym.symtype = self.symbol_types.NUMBER

        elif self.current_char == '-':  # connection operator ->
            self.get_next_char()
            if self.current_char == '>':
                sym.symtype = self.symbol_types.CONNECTION_OP
            self.get_next_char()

        elif self.current_char == ';':
            sym.symtype = self.symbol_types.SEMICOLON
            self.get_next_char()

        elif self.current_char == ',':
            sym.symtype = self.symbol_types.COMMA
            self.get_next_char()

        elif self.current_char == '.':
            sym.symtype = self.symbol_types.DOT
            self.get_next_char()

        elif self.current_char == '(':
            sym.symtype = self.symbol_types.OPENPAREN
            self.get_next_char()

        elif self.current_char == ')':
            sym.symtype = self.symbol_types.CLOSEPAREN
            self.get_next_char()

        elif self.current_char == '':
            sym.symtype = self.symbol_types.EOF

        else:
            self.get_next_char()

        print(sym.symtype, file=DEBUG)
        return sym

    def get_name(self):
        name = self.current_char
        self.get_next_char()
        while self.current_char.isalnum():
            name += self.current_char
            self.get_next_char()
        return name

    def get_number(self):
        numstr = self.current_char
        self.get_next_char()
        while self.current_char.isdigit():
            numstr += self.current_char
            self.get_next_char()
        return int(numstr, base=10)
