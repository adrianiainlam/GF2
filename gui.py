"""Implement the graphical user interface for the Logic Simulator.

Used in the Logic Simulator project to enable the user to run the simulation
or adjust the network properties.

Classes:
--------
MyGLCanvas - handles all canvas drawing operations.
Gui - configures the main window and all the widgets.
"""
import wx
import wx.glcanvas as wxcanvas
from OpenGL import GL, GLUT

from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner
from parse import Parser
import os


import builtins


class MyGLCanvas(wxcanvas.GLCanvas):
    """Handle all drawing operations.

    This class contains functions for drawing onto the canvas. It
    also contains handlers for events relating to the canvas.

    Parameters
    ----------
    parent: parent window.
    devices: instance of the devices.Devices() class.
    monitors: instance of the monitors.Monitors() class.

    Public methods
    --------------
    init_gl(self): Configures the OpenGL context.

    render(self, text): Handles all drawing operations.

    on_paint(self, event): Handles the paint event.

    on_size(self, event): Handles the canvas resize event.

    on_mouse(self, event): Handles mouse events.

    render_text(self, text, x_pos, y_pos): Handles text drawing operations.

    draw_signal(self, signal_list, x_start, x_step, y_low, y_high):
    Draws one signal onto the canvas.

    def draw_all_signals(self): Draws all signals, together with their labels,
                                axes, and other decorations.

    draw_time_axis(self, max_sig_len, x_step, init_orig):
    Draws a time axis above the first signal.

    """

    def __init__(self, parent, devices, monitors):
        """Initialise canvas properties and useful variables."""
        super().__init__(parent, -1,
                         attribList=[wxcanvas.WX_GL_RGBA,
                                     wxcanvas.WX_GL_DOUBLEBUFFER,
                                     wxcanvas.WX_GL_DEPTH_SIZE, 16, 0])
        GLUT.glutInit()
        self.init = False
        self.context = wxcanvas.GLContext(self)
        self.devices = devices
        self.monitors = monitors

        self.msg = ""

        # Initialise variables for panning
        self.pan_x = 0
        self.pan_y = 0
        self.last_mouse_x = 0  # Previous mouse x position
        self.last_mouse_y = 0  # Previous mouse y position

        # Initialise variables for zooming
        self.zoom = 1

        # Bind events to the canvas
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)

    def init_gl(self):
        """Configure and initialise the OpenGL context."""
        size = self.GetClientSize()
        self.SetCurrent(self.context)
        GL.glDrawBuffer(GL.GL_BACK)
        GL.glClearColor(1.0, 1.0, 1.0, 0.0)
        GL.glViewport(0, 0, size.width, size.height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(0, size.width, 0, size.height, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glTranslated(self.pan_x, self.pan_y, 0.0)
        GL.glScaled(self.zoom, self.zoom, self.zoom)

    def draw_signal(self, signal_list, x_start, x_step, y_low, y_high):
        """
        Draws one signal onto the canvas.

        signal_list: A list containing the signal levels defined in
                     Devices. signal_list[0] would correspond to the
                     signal level between time cycles 0 and 1, etc.
        x_start: The starting x-coordinate of the signal.
        x_step: x-coordinate of the (k+1)th cycle, minus x-coordinate
                of the kth cycle.
        y_low: y-coordinate of a LOW level signal.
        y_high: y-coordinate of a HIGH level signal.
        """
        GL.glColor3f(0.0, 0.0, 1.0)  # Blue
        GL.glBegin(GL.GL_LINE_STRIP)
        prev_sig_blank = False
        x = x_start
        for signal in signal_list:
            if signal == self.devices.BLANK:
                if not prev_sig_blank:
                    GL.glEnd()
                    prev_sig_blank = True
            else:
                if prev_sig_blank:
                    GL.glBegin(GL.GL_LINE_STRIP)
                    prev_sig_blank = False

                if signal == self.devices.HIGH:
                    y = y_next = y_high
                elif signal == self.devices.LOW:
                    y = y_next = y_low
                elif signal == self.devices.RISING:
                    y = y_low
                    y_next = y_high
                elif signal == self.devices.FALLING:
                    y = y_high
                    y_next = y_low

                GL.glVertex2f(x, y)
                GL.glVertex2f(x + x_step, y_next)
            x += x_step

        if not prev_sig_blank:
            GL.glEnd()

    def draw_all_signals(self):
        """
        Draws all signals, together with their labels, axes, and other
        decorations.

        By default, the signals are obtained from
        self.monitor.monitors_dictionary, and the signal names from
        self.devices.get_signal_name(). If, however,
        self.debug_dict is defined, then it will use that as
        the monitors dictionary, and use device_id and output_id
        in the labels.
        """
        init_orig = {'x': 30, 'y': 500}
        current_orig = init_orig.copy()
        x_step = 20
        y_sig_sep = -75
        y_high_low_diff = 25

        max_sig_len = 0

        if not hasattr(self, 'debug_dict'):
            mon_dict = self.monitors.monitors_dictionary
            get_signal_name = self.devices.get_signal_name
        else:
            mon_dict = self.debug_dict

            def get_signal_name(device_id, output_id):
                return "Testing, device_id=%d, output_id=%d" % \
                       (device_id, output_id)

        def mon_dict_sorter(entry_tuple):
            (device_id, output_id) = entry_tuple
            return get_signal_name(device_id, output_id)

        for (device_id, output_id) in sorted(mon_dict, key=mon_dict_sorter):
            monitor_name = get_signal_name(device_id, output_id)
            signal_list = mon_dict[(device_id, output_id)]
            max_sig_len = max(max_sig_len, len(signal_list))

            x = current_orig['x']
            y_low = current_orig['y']
            y_high = y_low + y_high_low_diff

            # Label monitor name and signal levels
            self.render_text('hi', x - 20, y_high - 3)
            self.render_text('lo', x - 20, y_low - 3)
            self.render_text(monitor_name, x, y_low - 18)

            # Then draw signal traces
            self.draw_signal(signal_list, x, x_step, y_low, y_high)
            current_orig['y'] += y_sig_sep

        # Now draw a time axis on top
        if max_sig_len != 0:
            self.draw_time_axis(max_sig_len, x_step, init_orig)

    def draw_time_axis(self, max_sig_len, x_step, init_orig):
        """
        Draws a time axis above the first signal.

        max_sig_len: The length of the longest signal, in number of
                     cycles.
        x_step: x-coordinate of the (k+1)th cycle, minus x-coordinate
                of the kth cycle.
        init_orig: a dictionary with 'x' and 'y' as keys, whose values
                   are the x- and y- coordinates of the origin of
                   the first signal.

        Within this function, a constant, `tick_sep', is used to
        control the separation between ticks on the axis.
        """
        # tick_sep: Seperation between ticks on the axis.
        # A possible extension is to allow user input for this
        # value in the UI.
        tick_sep = 2

        GL.glColor3f(0, 0, 0)
        arrow_start = {
            'x': init_orig['x'] - 5,
            'y': init_orig['y'] + 50
        }
        # arrow_len = smallest int above max_sig_len that is
        #             a multiple of tick_sep
        arrow_len = \
            ((max_sig_len + tick_sep - 1) // tick_sep) * tick_sep
        arrow_end = {
            'x': arrow_start['x'] + arrow_len * x_step + 20,
            'y': arrow_start['y']
        }
        GL.glBegin(GL.GL_LINE_STRIP)
        # Draw the horizontal line of the arrow
        GL.glVertex2f(arrow_start['x'], arrow_start['y'])
        GL.glVertex2f(arrow_end['x'], arrow_end['y'])
        # Draw the upward pointing bit
        GL.glVertex2f(arrow_end['x'] - 5, arrow_end['y'] + 3)
        GL.glEnd()
        # Draw the downward pointing bit
        GL.glBegin(GL.GL_LINE_STRIP)
        GL.glVertex2f(arrow_end['x'], arrow_end['y'])
        GL.glVertex2f(arrow_end['x'] - 5, arrow_end['y'] - 3)
        GL.glEnd()
        # Draw ticks every tick_sep cycles
        for i in range(0, arrow_len + 1, tick_sep):
            tick_xpos = init_orig['x'] + i * x_step
            GL.glBegin(GL.GL_LINE_STRIP)
            GL.glVertex2f(tick_xpos, arrow_start['y'] - 3)
            GL.glVertex2f(tick_xpos, arrow_start['y'] + 3)
            GL.glEnd()

            # Adjustment for tick label: shift label slightly
            # to the left, depending on how many characters in
            # the label, such that the middle of the label is
            # approx right on top of the tick
            tick_label_adj = -4 * len(str(i))
            self.render_text(str(i), tick_xpos + tick_label_adj,
                             arrow_start['y'] + 5)
        self.render_text('t / cycle', arrow_end['x'] + 10,
                         arrow_end['y'] - 3)

    def render(self, text=None):
        """Handle all drawing operations."""
        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        # Clear everything
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        # Draw specified text at position (10, 10)
        # Draw message text at position (10, 10), keeping the same
        # on-screen location even with panning and zooming.
        if text is not None:
            self.msg = text
        xpos_transformed = (10 - self.pan_x) / self.zoom
        ypos_transformed = (10 - self.pan_y) / self.zoom
        self.render_text(self.msg, xpos_transformed, ypos_transformed)

        # Now draw the signals
        self.draw_all_signals()

        # We have been drawing to the back buffer, flush the graphics pipeline
        # and swap the back buffer to the front
        GL.glFlush()
        self.SwapBuffers()

    def on_paint(self, event):
        """Handle the paint event."""
        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        size = self.GetClientSize()
        self.render()

    def on_size(self, event):
        """Handle the canvas resize event."""
        # Forces reconfiguration of the viewport, modelview and projection
        # matrices on the next paint event
        self.init = False

    def on_mouse(self, event):
        """Handle mouse events."""
        if event.ButtonDown():
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
        if event.Dragging():
            self.pan_x += event.GetX() - self.last_mouse_x
            self.pan_y -= event.GetY() - self.last_mouse_y
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            self.init = False
        if event.GetWheelRotation() < 0:
            self.zoom *= (1.0 + (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.init = False
        if event.GetWheelRotation() > 0:
            self.zoom /= (1.0 - (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.init = False
        self.Refresh()  # Triggers the paint event

    def render_text(self, text, x_pos, y_pos):
        """Handle text drawing operations."""
        GL.glColor3f(0.0, 0.0, 0.0)  # Text is black
        GL.glRasterPos2f(x_pos, y_pos)
        font = GLUT.GLUT_BITMAP_HELVETICA_12

        for character in text:
            if character == '\n':
                y_pos = y_pos - 20
                GL.glRasterPos2f(x_pos, y_pos)
            else:
                GLUT.glutBitmapCharacter(font, ord(character))


class Gui(wx.Frame):
    """Configure the main window and all the widgets.

    This class provides a graphical user interface for the Logic Simulator and
    enables the user to change the circuit properties and run simulations.

    Parameters
    ----------
    title: title of the window.

    Public methods
    --------------
    on_menu(self, event): Event handler for the file menu.

    on_spin(self, event): Event handler for when the user changes the spin
                          control value.

    on_run(self, event): Event handler for when the user clicks the run button.

    on_continue(self, event): Event handler for when the user clicks the
                              continue button.

    on_restart(self, event): Event handler for when the user clicks the
                             continue button.

    on_checkbox(self,event): Event handler for when the user checks or unchecks
                             a checkbox.

    on_checklist(self,event): Event handler for when the user checks or
                              unchecksan element of the checkboxlist.

    on_retrieve(self,event): Event handler for when the user clicks the
                             retrieve button.

    run_network(self, cycles): Function running the network for the specified
                               number of simulation cycles.

    """

    def __init__(self, title, path, names, devices, network, monitors):
        """Initialise widgets and layout."""
        super().__init__(parent=None, title=title, size=(800, 600))

        # Creating global variables
        self.monitors = monitors
        self.devices = devices
        self.names = names
        self.network = network
        self.cycles_completed = 0

        # Create and setup the file menu
        fileMenu = wx.Menu()
        menuBar = wx.MenuBar()
        fileMenu.Append(wx.ID_ABOUT, _(u"&About"))
        fileMenu.Append(wx.ID_EXIT, _(u"&Exit"))
        menuBar.Append(fileMenu, _(u"&File"))
        self.SetMenuBar(menuBar)
        self.Bind(wx.EVT_MENU, self.on_menu)

        # Create UI elements and init
        self.cycles_text = wx.StaticText(self, wx.ID_ANY, _("Nr of cycles"))
        self.spin = wx.SpinCtrl(self, wx.ID_ANY, "10")
        self.run_button = wx.Button(self, wx.ID_ANY, _("Run"))
        self.continue_button = wx.Button(self, wx.ID_ANY, _("Continue"))
        self.restart_button = wx.Button(self, wx.ID_ANY, _("Restart"))
        self.switches_text = wx.StaticText(self, wx.ID_ANY, _("Switches"))
        self.monitors_text = wx.StaticText(self, wx.ID_ANY,
                                           _("Monitored Outputs"))

        self.continue_button.Disable()              # Init of continue button

        self.canvas = MyGLCanvas(self, devices, monitors)

        # Creating sizers
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        side_sizer = wx.BoxSizer(wx.VERTICAL)
        switches_sizer = wx.BoxSizer(wx.VERTICAL)
        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Setting hierarchy of sizers and UI elements
        main_sizer.Add(self.canvas, 5, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(side_sizer, 1, wx.ALL, 5)
        side_sizer.Add(self.cycles_text, 1, wx.TOP, 10)
        side_sizer.Add(self.spin, 1, wx.ALL, 5)
        side_sizer.Add(buttons_sizer)
        buttons_sizer.Add(self.run_button, 1, wx.ALL, 5)
        buttons_sizer.Add(self.continue_button, 1, wx.ALL, 5)
        side_sizer.Add(self.restart_button, 1, wx.ALL, 5)
        side_sizer.Add(self.switches_text)
        side_sizer.Add(switches_sizer, 1, wx.ALL, 5)
        side_sizer.Add(self.monitors_text, 1, wx.TOP, 10)

        # Starting monitors UI
        # Retrieve and create names list of showed/hidden monitors.
        [monitored_name_list, non_monitored_name_list] \
            = self.monitors.get_signal_names()
        monitors_list = []
        for mon_name in monitored_name_list:
            monitors_list.append([mon_name, True])
        for mon_name in non_monitored_name_list:
            monitors_list.append([mon_name, False])

        # Sort the monitors list.
        # Using LooseVersion to sort the list makes sure that
        # e.g. "a10" gets sorted after "a2", which is not true
        # if sorted simply as strings.
        # Note that semantically it may be better to use natsort
        # instead of LooseVersion, but natsort is not in the
        # standard library while distutils.version is.
        from distutils.version import LooseVersion
        monitors_list = sorted(monitors_list, key=lambda mon_status:
                               LooseVersion(mon_status[0]))
        choices_list = [x for [x, y] in monitors_list]

        # Setup parameters and create monitors CheckListBox
        # Estimate length, width and create size of CheckListBox
        length_checklistbox = min(len(choices_list)*21, 250)
        width_checklistbox = min((max([len(i) for i in choices_list])*9+120),
                                 300)
        size_checklistbox = wx.Size(width_checklistbox, length_checklistbox)
        self.monitors_checklistbox = wx.CheckListBox(
                                     self, choices=choices_list,
                                     size=size_checklistbox)
        side_sizer.Add(self.monitors_checklistbox)
        self.monitors_checklistbox.Enable()

        # Setting which switches are checked
        checked_strings = [x[0] for x in monitors_list if x[1]]
        self.monitors_checklistbox.SetCheckedStrings(checked_strings)

        # Starting switches UI
        # Preparing switches name list and other parameters.
        switches_list = [x for x in self.devices.devices_list
                         if x.device_kind == self.devices.SWITCH]
        switches_state_list = []
        for switch in switches_list:
            switch_state = switch.switch_state
            switches_state_list.append([switch,
                                        switch_state != self.devices.LOW])
        switches_list = sorted(switches_list, key=lambda sw:
                               self.names.get_name_string(sw.device_id))
        choices_list = [x for [x, y] in switches_state_list]
        column_number = 0  # Counter for column index of switch checkbox
        column_range = 4  # Parameter limiting the nr of checkboxes in a line
        row_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Setup checkboxes for switches
        for s in range(len(switches_state_list)):
            column_number = column_number + 1
            label = self.names.get_name_string(choices_list[s].device_id)
            self.checkbox = wx.CheckBox(self, label=label, name=label)
            self.checkbox.SetValue(switches_state_list[s][1])
            row_sizer.Add(self.checkbox, 0, wx.ALL, 5)
            if column_number == column_range and \
               s != len(switches_state_list) - 1:
                column_number = 0
                switches_sizer.Add(row_sizer)
                row_sizer = wx.BoxSizer(wx.HORIZONTAL)
        switches_sizer.Add(row_sizer)

        # Starting retrieve button UI
        retrieve_button = wx.Button(self, -1, _("Open definition file"))
        side_sizer.Add(retrieve_button, 1, wx.TOP, 5)

        # Setting events handling
        self.Bind(wx.EVT_CHECKBOX, self.on_checkbox)
        self.Bind(wx.EVT_CHECKLISTBOX, self.on_checklist)
        self.run_button.Bind(wx.EVT_BUTTON, self.on_run)
        self.continue_button.Bind(wx.EVT_BUTTON, self.on_continue)
        self.restart_button.Bind(wx.EVT_BUTTON, self.on_restart)
        retrieve_button.Bind(wx.EVT_BUTTON, self.on_retrieve)

        self.SetSizeHints(600, 600)
        self.SetSizer(main_sizer)

    def on_checkbox(self, event):
        """Handle the event when the user checks or unchecks a checkbox.

        The event will set the selected switch on the opened/closed state."""
        # Retrieving name and ID of the checkbox checked/unchecked.
        clicked = event.GetEventObject()
        switch_name = clicked.GetName()
        switch_id = self.names.query(switch_name)

        # Setting switch state using the devices method.
        switch_state = (self.devices.LOW if event.IsChecked() is False
                        else self.devices.HIGH)
        if self.devices.set_switch(switch_id, switch_state):
            self.canvas.render(_("Successfully set switch on ") + (
                               _("open") if event.IsChecked() is False
                               else _("closed")))
        else:
            self.canvas.render(_("Error! Invalid switch."))

    def on_checklist(self, event):
        """
        Handle the event when the user checks/unchecks an element of the
        checkboxlist.

        The event will show or hide an output from the monitor."""

        # Retrieving name of the list element checked/unchecked
        clicked = event.GetEventObject()
        device_string = event.GetString()
        index = event.GetInt()
        [device, port] = device_string.split(".") if "." in device_string \
            else (device_string, "")

        # Preparing IDs to feed to the monitors methods
        device_id = self.names.query(device)
        port_id = self.names.query(port)

        # Monitor operations and methods
        if (clicked.IsChecked(index)):
            monitor_error = self.monitors.make_monitor(device_id, port_id,
                                                       self.cycles_completed)
            if monitor_error == self.monitors.NO_ERROR:
                self.canvas.render(_("Successfully made monitor."))
            else:
                self.canvas.render(_("Error! Could not make monitor."))
        else:
            if self.monitors.remove_monitor(device_id, port_id):
                self.canvas.render(_("Successfully zapped monitor"))
            else:
                self.canvas.render(_("Error! Could not zap monitor."))

    def run_network(self, cycles):
        """Run the network for the specified number of simulation cycles.

        Return True if successful.
        """
        for _ in range(cycles):
            if self.network.execute_network():
                self.monitors.record_signals()
            else:
                self.canvas.render(_("Error! Network oscillating."))
                return False
        
        self.canvas.render((_("Ran for ")+str(cycles)+_(" cycles.")))
        return True

    def on_run(self, event):
        """Handle the event when the user clicks the run button."""
        self.cycles_completed = 0
        cycles = self.spin.GetValue()
        if cycles is not None:
            # Handling gui interactions
            self.continue_button.Enable()
            #self.monitors_checklistbox.Disable()

            # Reset output, print new running network and update nr cycles.
            self.monitors.reset_monitors()
            self.devices.cold_startup()
            if self.run_network(cycles):
                self.cycles_completed += cycles

    def on_continue(self, event):
        """Handle the event when the user clicks the continue button."""
        # Handling gui interactions
        #self.monitors_checklistbox.Disable()

        # Print continued network and update nr of cycles if successful.
        cycles = self.spin.GetValue()
        if cycles is not None:
            if self.run_network(cycles):
                self.cycles_completed += cycles
                self.canvas.render(_(_("Continued for ")+str(cycles)+_(" cycles. Total: ")+str(self.cycles_completed)))

    def on_restart(self, event):
        """Handle the event when the user clicks the restart button."""
        # Handling gui interactions
        self.monitors_checklistbox.Enable()
        self.continue_button.Disable()

        # Resetting monitors and parameters
        self.monitors.reset_monitors()
        self.devices.reset_devices()
        self.cycles_completed = 0
        self.spin.SetValue(10)

        # Force canvas to re-init positions etc.
        self.canvas.init = False
        self.canvas.pan_x = self.canvas.pan_y = 0
        self.canvas.zoom = 1
        self.canvas.render(_("Restarted"))

    def on_retrieve(self, event):
        """Handle the event when the user clicks the retrieve button.

        This is used to open the definition file and allow modifications."""
        # We set a flag to indicate to logsim that the GUI is to be restarted.
        # Then we close the interface and allow logsim to start an editor.
        # Afterwards, logsim would restart the GUI.
        self.edit_restart = True
        self.Close()

    def on_menu(self, event):
        """Handle the event when the user selects a menu item."""
        Id = event.GetId()
        if Id == wx.ID_EXIT:
            self.Close(True)
        if Id == wx.ID_ABOUT:
            wx.MessageBox("Logic Simulator\nCreated by S. Arulselvan, \
F. Freddi, A. I. Lam\n2018", "About Logsim", wx.ICON_INFORMATION | wx.OK)
