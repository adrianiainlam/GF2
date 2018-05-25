"""Parse the definition file and build the logic network.

Used in the Logic Simulator project to analyse the syntactic and semantic
correctness of the symbols received from the scanner and then builds the
logic network.

Classes
-------
Parser - parses the definition file and builds the logic network.
"""

from names import Names
from scanner import Symbol, Scanner



class Parser:

    """Parse the definition file and build the logic network.

    The parser deals with error handling. It analyses the syntactic and
    semantic correctness of the symbols it receives from the scanner, and
    then builds the logic network. If there are errors in the definition file,
    the parser detects this and tries to recover from it, giving helpful
    error messages.

    Parameters
    ----------
    names: instance of the names.Names() class.
    devices: instance of the devices.Devices() class.
    network: instance of the network.Network() class.
    monitors: instance of the monitors.Monitors() class.
    scanner: instance of the scanner.Scanner() class.

    Public methods
    --------------
    parse_network(self): Parses the circuit definition file.
    """

    def __init__(self, names, devices, network, monitors, scanner):
        """Initialise constants."""
        self._names = names
        self._devices = devices
        self._network = network
        self._monitors = monitors
        self._scanner = scanner

        self._current_sym = None
        self._syntax_err_cnt = 0  # TODO remember to update counter for
                                  # each error!

        # Defining all error types now using names.unique_error_codes NEED TO UPDATE
        #PARAMETER TO unique_error_codes IF CHANGING NUMBER OF ERROR TYPES
        [self.NO_END, self.NO_EOF, self.NO_DEVICE, self.NOT_VALID_DEVICE_TYPE, self.NO_NAME,
        self.NO_PARAMETER, self.NO_CLOSE_BRACKET, self.NO_PUNCTUATION, self.NO_CONNECT,
        self.NOT_VALID_OUTPUT, self.NO_CONNECTION_OP, self.NO_DOT, self.NOT_VALID_INPUT,
        self.NO_MONITOR, self.NO_SEMI_COLON] = self._names.unique_error_codes(15)

    def parse_network(self):
        """Parse the circuit definition file."""
        # For now just return True, so that userint and gui can run in the
        # skeleton code. When complete, should return False when there are
        # errors in the circuit definition file.

        ret = True  # return value, True = no errors, False = error

        ret = ret and self._parse_device_list()
        ret = self._parse_connect_list() and ret
        ret = ret and self._parse_monitor_list()

        # _current_sym should then be "END" keyword
        KEYWORD = self._scanner.symbol_types.KEYWORD
        EOF = self._scanner.symbol_types.EOF
        if self._current_sym.symtype != KEYWORD or \
           self._current_sym.symid != self._names.lookup(["END"])[0]:
            # error: expected "END"
            self.display_error(self.NO_END)
            return False
        else:
            # then we expect EOF
            self._current_sym = self._scanner.get_symbol()
            if self._current_sym.symtype != EOF:
                self.display_error(self.NO_EOF)
                return False

        return ret


    def _parse_device_list(self):
        """
        Parses the entire DEVICE list (DEVICE XOR x; AND a, b; ...)

        This function will get its initial symbol, and will read the
        next symbol to current_sym.
        """
        sym_t = self._scanner.symbol_types
        lookup = self._names.lookup

        ret = True

        self._current_sym = self._scanner.get_symbol()

        if self._current_sym.symtype != sym_t.KEYWORD or \
           self._current_sym.symid != lookup(["DEVICE"])[0]:
            # error stating Keyword "DEVICE" not found at start
            self.display_error(self.NO_DEVICE)
            # TODO then proceed to find the next keyword, terminating
            # if EOF reached.
            #   if DEVICE found, restart from here.
            #   elif CONNECT found, pass to CONNECT
            #   elif MONITOR found, pass to MONITOR
            #   else, EOF reached, terminate
            return False  # TODO designate error codes

        self._current_sym = self._scanner.get_symbol()

        while self._current_sym.symtype not in [sym_t.KEYWORD, sym_t.EOF]:
            ret = ret and self._parse_device_def()
            self._current_sym = self._scanner.get_symbol()

        if self._current_sym.symtype == sym_t.EOF:
            return False
        return ret



    def _parse_device_def(self):
        """
        Parses one line of the device definition (AND a1, a2;)

        Expects current_sym to have already been updated to
        the next symbol.
        """
        COMMA = self._scanner.symbol_types.COMMA
        SEMICOLON = self._scanner.symbol_types.SEMICOLON

        ret = True

        ret = ret and self._parse_device_type()

        ret = ret and self._parse_device()

        while self._current_sym.symtype == COMMA and ret:
            ret = ret and self._parse_device()

        if self._current_sym.symtype not in [COMMA, SEMICOLON]:
            # TODO Error expected comma or semicolon
            self.display_error(self.NO_PUNCTUATION)
            return False
        # if this part reached then current_sym must be SEMICOLON,
        # hence we terminate
        return ret

    def _parse_device_type(self):
        """
        Parses the device type within a device definition.

        Expects current_sym to have already been updated to
        the next symbol.
        Will NOT update current_sym.
        """
        NAME_CAPS = self._scanner.symbol_types.NAME_CAPS
        if self._current_sym.symtype != NAME_CAPS:
            # expected DeviceType (all-caps identifier)
            self.display_error(self.NOT_VALID_DEVICE_TYPE)
            return False
        return True

    def _parse_device(self):
        """
        Parses a specific device (ck(2)).

        Will get its own initial symbol.
        Will update current_sym to next symbol.
        """
        COMMA = self._scanner.symbol_types.COMMA
        SEMICOLON = self._scanner.symbol_types.SEMICOLON
        OPENPAREN = self._scanner.symbol_types.OPENPAREN
        CLOSEPAREN = self._scanner.symbol_types.CLOSEPAREN
        NUMBER = self._scanner.symbol_types.NUMBER

        ret = True

        ret = ret and self._parse_device_name()

        self._current_sym = self._scanner.get_symbol()

        # BELOW: why did I define this? TODO remove if not needed
        #device_has_param = False
        if self._current_sym.symtype == OPENPAREN:
            #device_has_param = True
            # get number and closeparen
            self._current_sym = self._scanner.get_symbol()
            if self._current_sym.symtype != NUMBER:
                # ERROR
                self.display_error(self.NO_PARAMETER)
                return False
            self._current_sym = self._scanner.get_symbol()
            if self._current_sym.symtype != CLOSEPAREN:
                # Error
                self.display_error(self.NO_CLOSE_BRACKET)
                return False
            self._current_sym = self._scanner.get_symbol()

        return ret  ## comma/semicolon checked in device_def


    def _parse_device_name(self, getsym=True):
        """
        Parses the name of a device.'

        Will get its own initial symbol if getsym == True.
        Will NOT update current_sym.
        """
        NAME_CAPS = self._scanner.symbol_types.NAME_CAPS
        NAME_CAPSNUM = self._scanner.symbol_types.NAME_CAPSNUM
        NAME_ALNUM = self._scanner.symbol_types.NAME_ALNUM

        NAME_ANY = [NAME_CAPS, NAME_CAPSNUM, NAME_ALNUM]

        if getsym:
            self._current_sym = self._scanner.get_symbol()

        if self._current_sym.symtype not in NAME_ANY:
            # ERROR
            # expected device name
            self.display_error(self.NO_NAME)
            # skip to next comma or semicolon
            return False
        return True


    def _parse_connect_list(self):
        """
        Parses the entire CONNECT list.

        Assumes current_sym has been updated with the next symbol.
        Will update current_sym with the next symbol.
        """
        ret = True

        KEYWORD = self._scanner.symbol_types.KEYWORD
        EOF = self._scanner.symbol_types.EOF

        if self._current_sym.symtype != KEYWORD or \
           self._current_sym.symid != self._names.lookup(["CONNECT"])[0]:
            # error
            self.display_error(self.NO_CONNECT)
            # recovery: see _parse_device_list
            return False

        self._current_sym = self._scanner.get_symbol()

        while self._current_sym.symtype != KEYWORD and ret:
            ret = ret and self._parse_connection()
            self._current_sym = self._scanner.get_symbol()

        if self._current_sym.symtype == EOF:
            return False
        return ret


    def _parse_connection(self):
        """
        Parse one connection.

        Assumes the initial symbol has been updated in current_sym.
        Will update current_sym with the next symbol.
        """
        ret = True

        ret = ret and self._parse_output()

        CONNECTION_OP = self._scanner.symbol_types.CONNECTION_OP
        if self._current_sym.symtype != CONNECTION_OP:
            # error
            self.display_error(self.NO_CONNECTION_OP)
            return False

        ret = ret and self._parse_input()

        COMMA = self._scanner.symbol_types.COMMA
        SEMICOLON = self._scanner.symbol_types.SEMICOLON

        self._current_sym = self._scanner.get_symbol()
        while self._current_sym.symtype == COMMA:
            ret = ret and self._parse_input()
            self._current_sym = self._scanner.get_symbol()

        if self._current_sym.symtype != SEMICOLON:
            # error
            self.display_error(self.NO_SEMI_COLON)
            return False
        return ret


    def _parse_output(self):
        """
        Parse an output name.

        Assumes current_sym has been updated with initial symbol.
        Will update current_sym with next symbol.
        """
        ret = True
        # get_symbol() has already been called by _parse_connection_list()
        # for keyword check
        ret = ret and self._parse_device_name(getsym=False)

        self._current_sym = self._scanner.get_symbol()
        # current sym should then now be either
        # the optional ".", or "->" (to be checked by _parse_connection())

        DOT = self._scanner.symbol_types.DOT
        SEMICOLON = self._scanner.symbol_types.SEMICOLON
        NAME_CAPS = self._scanner.symbol_types.NAME_CAPS

        if self._current_sym.symtype == DOT:
            # next symbol should then be output pin
            self._current_sym = self._scanner.get_symbol()
            if self._current_sym.symtype != NAME_CAPS:
                # Error
                # output pin is not all capital letters
                self.display_error(self.NOT_VALID_OUTPUT)
                return False

            self._current_sym = self._scanner.get_symbol()
        return ret


    def _parse_input(self):
        """
        Parse an input name.

        Will update its own initial symbol into current_sym.
        Will update current_sym with next symbol.
        """
        ret = True

        ret = ret and self._parse_device_name()

        self._current_sym = self._scanner.get_symbol()

        DOT = self._scanner.symbol_types.DOT
        NAME_CAPSNUM = self._scanner.symbol_types.NAME_CAPSNUM
        NAME_CAPS = self._scanner.symbol_types.NAME_CAPS

        if self._current_sym.symtype != DOT:
            # error
            self.display_error(self.NO_DOT)
            return False
        self._current_sym = self._scanner.get_symbol()
        if self._current_sym.symtype not in [NAME_CAPSNUM, NAME_CAPS]:
            # error invalid input pin
            self.display_error(self.NOT_VALID_INPUT)
            return False
        return ret

    def _parse_monitor_list(self):
        """
        Parse the MONITOR list.

        Expect the initial symbol to have been updated in current_sym.
        Will update current_sym with the next symbol.
        """
        ret = True

        KEYWORD = self._scanner.symbol_types.KEYWORD
        EOF = self._scanner.symbol_types.EOF
        COMMA = self._scanner.symbol_types.COMMA

        if self._current_sym.symtype != KEYWORD or \
           self._current_sym.symid != self._names.lookup(["MONITOR"])[0]:
            # error
            self.display_error(self.NO_MONITOR)
            # recovery: see _parse_device_list()
            return False

        self._current_sym = self._scanner.get_symbol()

        ret = ret and self._parse_output()

        while self._current_sym.symtype == COMMA:
            self._current_sym = self._scanner.get_symbol()
            ret = ret and self._parse_output()

        if self._current_sym.symtype == EOF:
            return False
        return ret

    def display_error(self, error_type):
        self._syntax_err_cnt += 1
        self.boilerplate_error()
        if error_type == self.NO_DEVICE:
            print("KeywordError: missing keyword: DEVICE")
        elif error_type == self.NO_END:
            print("KeywordError: missing keyword: END")
        elif error_type == self.NO_MONITOR:
            print("KeywordError: missing keyword: MONITOR")
        elif error_type == self.NO_CONNECT:
            print("KeywordError: missing keyword: CONNECT")
        elif error_type == self.NO_EOF:
            print("FileError: Expected definition file to end here")
        elif error_type == self.NOT_VALID_DEVICE_TYPE:
            print("DeviceError: Not a valid device type")
        elif error_type == self.NO_NAME:
            print("DeviceError: Missing device name")
        elif error_type == self.NO_PARAMETER:
            print("DeviceError: Missing input parameter specified")
        elif error_type == self.NO_CLOSE_BRACKET:
            print("DeviceError: Missing closing parentheses")
        elif error_type == self.NO_PUNCTUATION:
            print("FileError: Missing comma or semi-colon")
        elif error_type == self.NOT_VALID_OUTPUT:
            print("ConnectionError: Not a valid device output")
        elif error_type == self.NOT_VALID_INPUT:
            print("ConnectionError: Not a valid device input")
        elif error_type == self.NO_CONNECTION_OP:
            print("ConnectionError: Missing connection operator \"->\" ")
        elif error_type == self.NO_DOT:
            print("ConnectionError: Missing input operator \".\" ")
        elif error_type == self.NO_SEMI_COLON:
            print("FileError: Missing semi-colon to separate connections")






    def boilerplate_error(self):
        path = self._scanner.path
        std_string = "File \"{}\", line {}"
        print("Traceback:", std_string.format(path, self._current_sym.linenum))
        print('\t', self._scanner.filelines[self._current_sym.linenum], end='')
        print('\t', ' '*(self._current_sym.colnum -1)+ '^')
