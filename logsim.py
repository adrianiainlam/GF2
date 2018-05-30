#!/usr/bin/env python3
"""Parse command line options and arguments for the Logic Simulator.

This script parses options and arguments specified on the command line, and
runs either the command line user interface or the graphical user interface.

Usage
-----
Show help: logsim.py -h
Command line user interface: logsim.py -c <file path>
Graphical user interface: logsim.py <file path>
"""
import getopt
import sys

import wx

from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner
from parse import Parser
from userint import UserInterface
from gui import Gui


def main(arg_list):
    """Parse the command line options and arguments specified in arg_list.

    Run either the command line user interface, the graphical user interface,
    or display the usage message.
    """
    usage_message = ("Usage:\n"
                     "Show help: logsim.py -h\n"
                     "Command line user interface: logsim.py -c <file path>\n"
                     "Graphical user interface: logsim.py <file path>")
    try:
        options, arguments = getopt.getopt(arg_list, "hc:")
    except getopt.GetoptError:
        print("Error: invalid command line arguments\n")
        print(usage_message)
        sys.exit()

    # Initialise instances of the four inner simulator classes
    names = Names()
    devices = Devices(names)
    network = Network(names, devices)
    monitors = Monitors(names, devices, network)

    for option, path in options:
        if option == "-h":  # print the usage message
            print(usage_message)
            sys.exit()
        elif option == "-c":  # use the command line user interface
            scanner = Scanner(path, names)
            parser = Parser(names, devices, network, monitors, scanner)
            if parser.parse_network():
                # Initialise an instance of the userint.UserInterface() class
                userint = UserInterface(names, devices, network, monitors)
                userint.command_interface()

    if not options:  # no option given, use the graphical user interface

        if len(arguments) != 1:  # wrong number of arguments
            print("Error: one file path required\n")
            print(usage_message)
            sys.exit()

        [path] = arguments
        scanner = Scanner(path, names)
        parser = Parser(names, devices, network, monitors, scanner)
        if parser.parse_network():
            # Initialise an instance of the gui.Gui() class
            app = wx.App()
            gui = Gui("Logic Simulator", path, names, devices, network,
                      monitors)
            gui.Show(True)
            app.MainLoop()

            while hasattr(gui, 'edit_restart'):
                # GUI terminated and set the edit_restart flag.
                # We open the file in an editor to allow the user
                # to change the file, then restart the GUI.
                del app
                run_editor(path)
                # Re-initialise everything
                names = Names()
                devices = Devices(names)
                network = Network(names, devices)
                monitors = Monitors(names, devices, network)
                scanner = Scanner(path, names)
                parser = Parser(names, devices, network, monitors, scanner)
                if parser.parse_network():
                    app = wx.App()
                    gui = Gui("Logic Simulator", path, names, devices,
                              network, monitors)
                    gui.Show(True)
                    app.MainLoop()
                else:
                    # Parser error messages would be enough, no need to
                    # re-inform users of parser failure.
                    break


def run_editor(path):
    # IMPORTANT NOTE:
    # ---------------
    #
    # Here it is assumed that this program will only
    # interact with the user who started it, i.e.
    #  - NOT as a network service taking inputs from
    #    untrusted sources, and
    #  - NOT started with elevated privilege (NOT RECOMMENDED)
    #    and subsequently taking inputs from unprivileged
    #    users, etc.
    #
    # If this program is to be adapted in the future, such
    # that ANY of the above conditions are not true, then
    # the following call to subprocess.run() must either
    # be removed or completely rewritten.
    #
    # To emphasize:
    # The following code will DROP TO A SHELL,
    # will allow ARBITRARY CODE EXECUTION,
    # and will allow READ-WRITE ACCESS TO LOCAL FILES.

    editor = find_editor()
    while True:
        if editor:
            import subprocess
            subprocess.run([editor, path])
            break
        else:
            print("Unable to find a text editor. Please " +
                  "enter the name or path of an editor, " +
                  "or type \"exit\" to terminate the program.")
            try:
                user_editor = input('> ')
            except EOFError:
                exit(0)
            if user_editor == "exit":
                exit(0)
            import shutil
            editor = shutil.which(user_editor)


def find_editor():
    import os
    import shutil

    editors = []

    # check environment variables
    if 'VISUAL' in os.environ:
        editors.append(os.environ['VISUAL'])
    if 'EDITOR' in os.environ:
        editor.append(os.environ['EDITOR'])

    # a list of common editors to try
    editors += ['emacs', 'nano', 'gedit', 'vim', 'vi', 'ed']

    for i in editors:
        if shutil.which(i):
            return i
    return None


if __name__ == "__main__":
    main(sys.argv[1:])
