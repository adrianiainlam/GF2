"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Scanner - reads definition file and translates characters into symbols.
"""


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

    def get_symbol(self):
        """Return the symbol type and ID of the next sequence of characters.

        If the current character is not recognised, both symbol type and ID
        are assigned None. Note: this function is called again (recursively)
        if it encounters a comment or end of line.
        """
