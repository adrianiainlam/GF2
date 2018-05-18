"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Scanner - reads definition file and translates characters into symbols.
"""

from enum import Enum


class Symbol():
    def __init__(self, symtype, symid, line, linenum, colnum):
        self.symtype = symtype
        self.symid   = symid
        self.line    = line
        self.linenum = linenum
        self.colnum  = colnum


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
            self.fh = open(path, mode='rt')
        except IOError:
            print("Failed to open %s for reading. Exiting." % path,
                  file=sys.stderr)
            sys.exit(1)

        self.names = names
        #self.symbol_type_list = [
        #    self.COMMA, self.SEMICOLON, self.CONNECTION_OP,
        #    self.KEYWORD, self.NUMBER, self.NAME, self.EOF,
        #    self
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
        self.current_line_num = 1 # to be incremented when \n is read
        self.current_col_num = 0 # to be incremented on first read


    def get_next_char(self):
        #self.current_char = self.fh.read(1)
        #self.current_col_num += 1
        #if self.current_char == '\n':
        #    self.current_line_num += 1
        #    self.current_
        if self.current_col_num == 0:
            self.current_line = self.fh.readline()
            self.current_line_num += 1

        if self.current_col_num >= len(self.current_line): # EOF reached
            self.current_char = ''
        else:
            self.current_char = self.current_line[self.currnet_col_num]

            if self.current_char == '\n':
                self.current_col_num = 0
            else:
                self.current_col_num += 1
        return self.current_char # for convenience
        
    def skip_to_next_symbol(self):
        #ch = self.get_next_char()
        ch = self.current_char
        isincomment = (ch == self.comment_start)

        while ch.isspace() or isincomment:
            ch = self.get_next_char()
            if isincomment:
                if ch == self.comment_end:
                    isincomment = False
                    ch = self.get_next_char()
            else:
                isincomment = (ch == self.comment_start)

        
    def get_symbol(self):
        """Return the symbol type and ID of the next sequence of characters.

        If the current character is not recognised, both symbol type and ID
        are assigned None. Note: this function is called again (recursively)
        if it encounters a comment or end of line.
        """
        self.skip_to_next_symbol()

        sym = Symbol(
            symtype=None, symid=None, line=self.current_line,
            linenum=self.current_line_num, colnum=self.current_col_num
        )
        if self.current_char.isalpha(): # name
            name_str = self.get_name()
            if name_str in self.keywords:
                sym.symtype = self.symbol_types.KEYWORD
            else:
                sym.symtype = self.symbol_types.NAME
            sym.symid = self.names.lookup([name_str])[0]

        elif self.current_char.isdigit(): # number
            sym.symid = self.get_number()
            symbol_type = self.symbol_types.NUMBER

        elif self.current_char == '-': # connection operator ->
            ch = self.get_next_char()
            if ch == '>':
                symbol_type = self.symbol_types.CONNECTION_OP
            self.get_next_char()
            
        elif self.current_char == ';':
            symbol_type = self.symbol_types.SEMICOLON
            self.get_next_char()

        elif self.current_char == ',':
            symbol_type = self.symbol_types.COMMA
            self.get_next_char()

        elif self.current_char == '.':
            symbol_type = self.symbol_types.DOT
            self.get_next_char()

        elif self.current_char == '(':
            symbol_type = self.symbol_types.OPENPAREN
            self.get_next_char()

        elif self.current_char == ')':
            symbol_type = self.symbol_types.CLOSEPAREN
            self.get_next_char()

        elif self.current_char == '':
            symbol_type = self.symbol_types.EOF

        else:
            self.get_next_char()
            
    def get_name():
        name = self.current_char
        self.get_next_char()
        while self.current_char.isalnum():
            name += self.current_char
            self.get_next_char()
        return name

    def get_number():
        numstr = self.current_char
        self.get_next_char()
        while self.current_char.isdigit():
            numstr += self.current_char
            self.get_next_char()
        return int(numstr, base=10)
