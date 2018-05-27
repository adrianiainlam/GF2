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

    render_text(self, text, x_pos, y_pos): Handles text drawing
                                           operations.
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

        # Initialise variables for panning
        self.pan_x = 0
        self.pan_y = 0
        self.last_mouse_x = 0  # previous mouse x position
        self.last_mouse_y = 0  # previous mouse y position

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
        GL.glColor3f(0.0, 0.0, 1.0)  # blue
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

        # FIXME sorting by IDs for testing/debug only, there may be better
        # ways to sort them
        for (device_id, output_id) in sorted(mon_dict):
            monitor_name = get_signal_name(device_id, output_id)
            signal_list = mon_dict[(device_id, output_id)]
            max_sig_len = max(max_sig_len, len(signal_list))

            x = current_orig['x']
            y_low = current_orig['y']
            y_high = y_low + y_high_low_diff

            # label monitor name and signal levels
            self.render_text('hi', x - 20, y_high - 3)
            self.render_text('lo', x - 20, y_low - 3)
            self.render_text(monitor_name, x, y_low - 18)

            # then draw signal traces
            self.draw_signal(signal_list, x, x_step, y_low, y_high)
            current_orig['y'] += y_sig_sep

        # now draw a time axis on top
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

            # adjustment for tick label: shift label slightly
            # to the left, depending on how many characters in
            # the label, such that the middle of the label is
            # approx right on top of the tick
            tick_label_adj = -4 * len(str(i))
            self.render_text(str(i), tick_xpos + tick_label_adj,
                             arrow_start['y'] + 5)
        self.render_text('t / cycle', arrow_end['x'] + 10,
                         arrow_end['y'] - 3)

    def render(self, text):
        """Handle all drawing operations."""
        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        # Clear everything
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        # Draw specified text at position (10, 10)
        self.render_text(text, 10, 10)

        # now draw the signals
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
        text = "".join(["Canvas redrawn on paint event, size is ",
                        str(size.width), ", ", str(size.height)])
        self.render(text)

    def on_size(self, event):
        """Handle the canvas resize event."""
        # Forces reconfiguration of the viewport, modelview and projection
        # matrices on the next paint event
        self.init = False

    def on_mouse(self, event):
        """Handle mouse events."""
        text = ""
        if event.ButtonDown():
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            text = "".join(["Mouse button pressed at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.ButtonUp():
            text = "".join(["Mouse button released at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.Leaving():
            text = "".join(["Mouse left canvas at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.Dragging():
            self.pan_x += event.GetX() - self.last_mouse_x
            self.pan_y -= event.GetY() - self.last_mouse_y
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            self.init = False
            text = "".join(["Mouse dragged to: ", str(event.GetX()),
                            ", ", str(event.GetY()), ". Pan is now: ",
                            str(self.pan_x), ", ", str(self.pan_y)])
        if event.GetWheelRotation() < 0:
            self.zoom *= (1.0 + (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.init = False
            text = "".join(["Negative mouse wheel rotation. Zoom is now: ",
                            str(self.zoom)])
        if event.GetWheelRotation() > 0:
            self.zoom /= (1.0 - (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.init = False
            text = "".join(["Positive mouse wheel rotation. Zoom is now: ",
                            str(self.zoom)])
        if text:
            self.render(text)
        else:
            self.Refresh()  # triggers the paint event

    def render_text(self, text, x_pos, y_pos):
        """Handle text drawing operations."""
        GL.glColor3f(0.0, 0.0, 0.0)  # text is black
        GL.glRasterPos2f(x_pos, y_pos)
        font = GLUT.GLUT_BITMAP_HELVETICA_12

        for character in text:
            if character == '\n':
                y_pos = y_pos - 20
                GL.glRasterPos2f(x_pos, y_pos)
            else:
                GLUT.glutBitmapCharacter(font, ord(character)) #ord(character) returns the ascii number corresponding to the string


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

    on_run_button(self, event): Event handler for when the user clicks the run
                                button.

    on_text_box(self, event): Event handler for when the user enters text.
    """

    def __init__(self, title, path, names, devices, network, monitors):
        """Initialise widgets and layout."""
        super().__init__(parent=None, title=title, size=(800, 600))

        self.monitors=monitors                      #making devices, names and network global varibales
        self.devices=devices
        self.names=names
        self.network = network
        self.cycles_completed=0

        # Configure the file menu
        fileMenu = wx.Menu()
        menuBar = wx.MenuBar()
        fileMenu.Append(wx.ID_ABOUT, "&About")
        fileMenu.Append(wx.ID_EXIT, "&Exit")
        menuBar.Append(fileMenu, "&File")  
        self.SetMenuBar(menuBar)
        self.Bind(wx.EVT_MENU, self.on_menu)

        #MY CODE FROM HERE ONWARDS
        
        self.cycles_text = wx.StaticText(self, wx.ID_ANY, "Nr of cycles")              #CREATION AND INIT OF UI ELEMENTS
        self.spin = wx.SpinCtrl(self, wx.ID_ANY, "10")              
        self.run_button = wx.Button(self, wx.ID_ANY, "Run")         
        self.continue_button = wx.Button(self, wx.ID_ANY, "Continue") 
        self.restart_button = wx.Button(self, wx.ID_ANY, "Restart")        
        self.switches_text = wx.StaticText(self, wx.ID_ANY, "Switches (closed is ticked)")  

        self.continue_button.Disable()                                          #init of continue button                                  

        self.canvas = MyGLCanvas(self, devices, monitors)

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)                                 #SIZERS
        side_sizer = wx.BoxSizer(wx.VERTICAL)
        switches_sizer = wx.BoxSizer(wx.VERTICAL)
        buttons_sizer=wx.BoxSizer(wx.HORIZONTAL)
        
        main_sizer.Add(self.canvas, 5, wx.EXPAND | wx.ALL, 5)                   #Assignement of sizer hierarchy and elements
        main_sizer.Add(side_sizer, 1, wx.ALL, 5)
        side_sizer.Add(self.cycles_text, 1, wx.TOP, 10)
        side_sizer.Add(self.spin, 1, wx.ALL, 5)
        side_sizer.Add(buttons_sizer)
        buttons_sizer.Add(self.run_button, 1, wx.ALL, 5)
        buttons_sizer.Add(self.continue_button, 1, wx.ALL, 5)
        side_sizer.Add(self.restart_button, 1, wx.ALL, 5)
        side_sizer.Add(self.switches_text)
        side_sizer.Add(switches_sizer, 1, wx.ALL, 5)

        [monitored_id_list,non_monitored_id_list]=monitors.get_signal_names()                           #MONITORS UI

        monitors_list=[]
        nr_mon=len(monitored_id_list)
        nr_non_mon=len(non_monitored_id_list)
        for i in range(nr_mon):                                                    #create list of names of monitors and showed/not showed on display from IDs
            monitor=monitored_id_list[i]
            device_name=self.names.get_name_string(monitor[0])
            port_name=self.names.get_name_string(monitor[1])
            monitors_list.append([device_name+"."+port_name,True])                          #True for monitored 
        for i in range(nr_mon,nr_mon+nr_non_mon):
            monitor=non_monitored_id_list[i]
            device_name=self.names.get_name_string(monitor[0])
            port_name=self.names.get_name_string(monitor[1])
            monitors_list.append([device_name+"."+port_name,False])                         #False as it is not monitored

        monitors_list=sorted(monitors_list)
                                                                                #create monitor checklistbox
        length_checklistbox=len(monitors_list)*21                                           #estimate length of CheckListBox
        width_checklistbox= max([len(i) for i in monitors_list])*9+120          #                    #estimate width of CheckListBox
        size_checklistbox=wx.Size(min((width_checklistbox),300),min(length_checklistbox,250))
        choices_list=[x for [x,y] in monitors_list]
        self.monitors_checklistbox=wx.CheckListBox(self,choices=choices_list,size=size_checklistbox)
        side_sizer.Add(self.monitors_checklistbox)
        self.monitors_checklistbox.Enable()

        for i in range(len(monitors_list)):                                   #initialise checked boxes
            if monitors_list[i][1]:
                self.monitors_checklistbox.SetCheckedStrings(monitors_list[i][0])


        switches_id_list=[x for x in self.devices.devices_list if x.device_kind==devices.SWITCH]                                     #SWITCHES UI
        switches_list=[]
        for i in range(len(switches_id_list)):
            switch=switches_id_list[i]
            switch_state=self.devices.get_device(switch).switch_state
            self.switches_list.append(switch,False if switch_state==devices.LOW else True)

        switches_list=sorted(switches_list)
        choices_list=[x for [x,y] in switches_list]
        column_number=0
        column_range=6
        row_sizer = wx.BoxSizer(wx.HORIZONTAL) 
        for s in range(len(switches_list)):                                #Setup checkboxes for switches
            column_number=column_number+1
            self.checkbox = wx.CheckBox(self,label=choices_list[s], name=choices_list[s])
            self.checkbox.SetValue(switches_list[s][1])
            row_sizer.Add(self.checkbox, 0, wx.ALL, 5)
            if (column_number==column_range and s!=(len(switches_list)-1)):
                column_number=0
                switches_sizer.Add(row_sizer)
                row_sizer=wx.BoxSizer(wx.HORIZONTAL) 
        switches_sizer.Add(row_sizer)

        retrieve_button = wx.Button(self,-1,"Open definition file")
        side_sizer.Add(retrieve_button,1,wx.TOP, 5)
        
        self.Bind(wx.EVT_CHECKBOX, self.OnChecked)                              #EVENTS HANDLING
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnChecklist)
        self.Bind(wx.EVT_BUTTON, self.OnGetData)
        self.run_button.Bind(wx.EVT_BUTTON, self.on_run_button)
        self.continue_button.Bind(wx.EVT_BUTTON, self.on_continue_button)
        self.restart_button.Bind(wx.EVT_BUTTON, self.on_restart_button)
        retrieve_button.Bind(wx.EVT_BUTTON, self.open_circuit_file_in_editor)

        self.SetSizeHints(600, 600)
        self.SetSizer(main_sizer)
                                                                     #DEFINITION OF FUNCTIONS AND EVENTS
    def OnChecked(self,event):        
        clicked = event.GetEventObject()
        # print(clicked.GetName())
        # print(event.IsChecked()*1) 
        switch_name = clicked.GetName()
        switch_id=self.names.query(switch_name)
        switch_state = (self.devices.LOW if event.IsChecked()==False else self.devices.HIGH) 
        if self.devices.set_switch(switch_id,switch_state):
            print("Successfully set switch.")
        else:
            print("Error! Invalid switch.")


    def OnChecklist(self,event):          #this is probably going to be useless in the final implementation
        clicked = event.GetEventObject()
        device_string=event.GetString()
        # print(device)
        # print(clicked.IsChecked(index)*1) 
        [device,port]=device_string.split(".")
        device_id = self.names.query(device)
        port_id = self.names.query(port)

        if (clicked.IsChecked(index)):
            monitor_error = self.monitors.make_monitor(device_id, port_id, self.cycles_completed)
            if monitor_error == self.monitors.NO_ERROR:
                print("Successfully made monitor.")
            else:
                print("Error! Could not make monitor.")
        else:
            if self.monitors.remove_monitor(device_id, port_id):
                print("Successfully zapped monitor")
            else:
                print("Error! Could not zap monitor.")


    def on_menu(self, event):                                   
        """Handle the event when the user selects a menu item."""
        Id = event.GetId()
        if Id == wx.ID_EXIT:
            self.Close(True)
        if Id == wx.ID_ABOUT:
            wx.MessageBox("Logic Simulator\nCreated by S. Arulselvan, F. Freddi, A. I. Lam\n2018",
                          "About Logsim", wx.ICON_INFORMATION | wx.OK)

    def run_network(self, cycles):            # used for on_run_button and on_continue_button
        """Run the network for the specified number of simulation cycles.

        Return True if successful.
        """
        for _ in range(cycles):
            if self.network.execute_network():
                self.monitors.record_signals()
            else:
                # TODO: change this, and other, `print()' calls to
                # a GUI message.
                print("Error! Network oscillating.")
                return False

        # TODO: confirm canvas signals are the same as those in console.
        # Afterwards, remove the display_signals() line.
        self.canvas.render('')
        self.monitors.display_signals()
        return True

    def on_run_button(self, event):
        """Handle the event when the user clicks the run button."""
        text = "Run button pressed."
 
        self.cycles_completed = 0
        cycles = self.spin.GetValue()
        if cycles is not None:
            self.continue_button.Enable()                       # handling interactions
            self.monitors_checklistbox.Disable() 
        
            self.monitors.reset_monitors()                    # if the number of cycles provided is valid
            print("".join(["Running for ", str(cycles), " cycles"]))
            self.devices.cold_startup()
            if self.run_network(cycles):
                self.cycles_completed += cycles

        self.canvas.render(text)
    
    def on_continue_button(self, event):
        """Handle the event when the user clicks the continue button."""
        text = "Continue button pressed."
        self.monitors_checklistbox.Disable()

        cycles = self.spin.GetValue()
        if cycles is not None:  
            if self.run_network(cycles):
                self.cycles_completed += cycles
                print(" ".join(["Continuing for", str(cycles), "cycles.",
                                "Total:", str(self.cycles_completed)]))

        self.canvas.render(text)

    def on_restart_button(self, event):
        """Handle the event when the user clicks the restart button."""
        text = "Restart button pressed."

        self.monitors_checklistbox.Enable()
        self.continue_button.Disable()

        self.monitors.reset_monitors()
        self.cycles_completed=0
        self.spin.SetValue(10)

        self.canvas.render(text)

    def open_circuit_file_in_editor(self, event):
        """
        We set a flag to indicate to logsim that the GUI is to be restarted.
        Then we close the interface and allow logsim to start an editor.
        Afterwards, logsim would restart the GUI.
        """
        self.edit_restart = True
        self.Close()






# TESTING ONLY
    def on_text_box(self, event):
        """Handle the event when the user enters text."""
        text_box_value = self.text_box.GetValue()
        text = "".join(["New text box value: ", text_box_value])
        self.canvas.render(text)

    def OnGetData(self,event):          # used for TESTING but will not be used in final version
        switches_dict = {}
        switches_list = []
        for i in self.switches_boxes:
            if i.IsChecked():
                n = i.GetName()
                switches_dict[n]="Checked"
                switches_list.append((n,"Checked"))
        monitors_dict = {}
        monitors_list = []
        for n in self.monitors_checklistbox.GetCheckedStrings():    #or GetCheckedItems retirns index of the choices vector that is checked
                monitors_dict[n]="Checked"
                monitors_list.append((n,"Checked"))

        print(switches_dict)
        print(switches_list)
        print(monitors_dict)
        print(monitors_list)

    def on_spin(self, event):                              # used for TESTING but not in final version of code
        """Handle the event when the user changes the spin control value."""
        spin_value = self.spin.GetValue()
        text = "".join(["New spin control value: ", str(int(spin_value))])
        self.canvas.render(text)

    def on_checkbox(self, event):
        """Handle the event when the user enters text."""
        checkbox_value = self.checkbox.GetValue()
        text = "".join(["New checkbox value: ", str(checkbox_value)])
        self.canvas.render(text)
