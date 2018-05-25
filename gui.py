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

        # Draw a sample signal trace
        GL.glColor3f(0.0, 0.0, 1.0)  # signal trace is blue - "3f stands for 3 dimensional and float"
        GL.glBegin(GL.GL_LINE_STRIP)
        for i in range(10):
            x = (i * 20) + 10
            x_next = (i * 20) + 30
            if i % 2 == 0:
                y = 75
            else:
                y = 100
            GL.glVertex2f(x, y)         #2f stands for 2 dimensional and float
            GL.glVertex2f(x_next, y)
        GL.glEnd()

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

        # Configure the file menu
        fileMenu = wx.Menu()
        menuBar = wx.MenuBar()
        fileMenu.Append(wx.ID_ABOUT, "&About")
        fileMenu.Append(wx.ID_EXIT, "&Exit")
        menuBar.Append(fileMenu, "&File")  
        self.SetMenuBar(menuBar)

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
        switches_sizer = wx.BoxSizer(wx.HORIZONTAL)
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

        [self.monitored_monitors_id_list,self.non_monitored_monitors_id_list]=monitors.get_signal_names()                           #MONITORS UI

        monitors_list=[]
        n=len(self.monitored_monitors_id_list)
        for i in range(n):                                                    #create list of names of monitors and showed/not showed on display
            monitor=self.monitored_monitors_id_list[i]
            device_name=names.get_name_string(monitor[0])
            port_name=names.get_name_string(monitor[1])
            monitors_list.append([device_name+"."+port_name,True])                          #True for monitored 
        for i in range(n,n+len(self.non_monitored_monitors_id_list)):
            monitor=self.non_monitored_monitors_id_list[i]
            device_name=names.get_name_string(monitor[0])
            port_name=names.get_name_string(monitor[1])
            monitors_list.append([device_name+"."+port_name,False])                         #False as it is not monitored

        monitors_list=sorted(monitors_list)
                                                                                #create monitor checklistbox
        length_checklistbox=len(monitors_list)*21                                           #estimate length of CheckListBox
        width_checklistbox= max([len(i) for i in monitors_list])*9+120                      #estimate width of CheckListBox
        size_checklistbox=wx.Size(min((width_checklistbox),300),min(length_checklistbox,250))
        choices_list=[x for [x,y] in monitors_list]
        self.monitors_checklistbox=wx.CheckListBox(self,choices=choices_list,size=size_checklistbox)
        side_sizer.Add(self.monitors_checklistbox)
        self.monitors_checklistbox.Enable()

        for i in range(len(monitors_list)):                                   #initialise checked boxes
            if monitors_list[i][1]:
                self.monitors_checklistbox.SetCheckedStrings(monitors_list[i][0])

# set the switches list of checkboxes as a grid so that the window does not keep expanding
# add button to view or upload a new code or save

        self.switches_id_list=[x for x in devices.devices_list if x.device_kind==devices.SWITCH]                                     #SWITCHES UI
        self.switches_list=[]
        for i in range(len(switches_id_list)):
            switch=self.switches_id_list[i]
            switch_state=devices.get_device(switch).switch_state
            switches_list.append(switch,False if switch_state==device.LOW else True)
        self.switches_boxes=[]

        switches_list=sorted(switches_list)
        choices_list=[x for [x,y] in switches_list]
        for s in range(len(switches_list)):                                     #Setup checkboxes for switches
            self.checkbox = wx.CheckBox(self,label=choices_list[s], name=choices_list[s])
            self.checkbox.SetValue(switches_list[s][1])
            switches_sizer.Add(self.checkbox, 0, wx.ALL, 5)
            self.switches_boxes.append(self.checkbox)

        retrieve_button = wx.Button(self,-1,"Retrieve Data")
        side_sizer.Add(retrieve_button,1,wx.TOP, 5)
        
        self.Bind(wx.EVT_CHECKBOX, self.OnChecked)                              #EVENTS HANDLING
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnChecklist)
        self.Bind(wx.EVT_BUTTON, self.OnGetData)
        self.run_button.Bind(wx.EVT_BUTTON, self.on_run_button)
        self.continue_button.Bind(wx.EVT_BUTTON, self.on_continue_button)
        self.restart_button.Bind(wx.EVT_BUTTON, self.on_restart_button)

        self.SetSizeHints(600, 600)
        self.SetSizer(main_sizer)
                                                                                #DEFINITION OF FUNCTIONS AND EVENTS
    def OnChecked(self,event):          #this is probably not going to be useless in the final implementation
        clicked = event.GetEventObject()
        print(clicked.GetName())
        print(event.IsChecked()*1) 
        # switch_id = clicked.GetName()
        #     switch_state = (event.IsChecked()*1) 
        #             if self.devices.set_switch(switch_id, switch_state):
        #                 print("Successfully set switch.")
        #             else:
        #                 print("Error! Invalid switch.")


    def OnChecklist(self,event):          #this is probably going to be useless in the final implementation
        clicked = event.GetEventObject()
        device_string=event.GetString()
        print(device)
        print(clicked.IsChecked(index)*1) 

        [device port]=device_string.split(".")
        device_id = self.names.query(device)
        port_id = self.names.query(port)

        monitor_error = self.monitors.make_monitor(device, port,
                                                    self.cycles_completed)
        if monitor_error == self.monitors.NO_ERROR:
            print("Successfully made monitor.")
        else:
            print("Error! Could not make monitor.")

    def OnGetData(self,event):          #this will need to be put into the on run and on continue (or it must be called by them)
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

    def on_menu(self, event):                                   
        """Handle the event when the user selects a menu item."""
        Id = event.GetId()
        if Id == wx.ID_EXIT:
            self.Close(True)
        if Id == wx.ID_ABOUT:
            wx.MessageBox("Logic Simulator\nCreated by S. Arulselvan, F. Freddi, A. I. Lam\n2018",
                          "About Logsim", wx.ICON_INFORMATION | wx.OK)

    def on_spin(self, event):
        """Handle the event when the user changes the spin control value."""
        spin_value = self.spin.GetValue()
        text = "".join(["New spin control value: ", str(int(spin_value))])
        self.canvas.render(text)

    def on_run_button(self, event):
        """Handle the event when the user clicks the run button."""
        text = "Run button pressed."
        self.continue_button.Enable()
        self.monitors_checklistbox.Disable()
        self.canvas.render(text)
    
    def on_continue_button(self, event):
        """Handle the event when the user clicks the continue button."""
        text = "Continue button pressed."
        self.monitors_checklistbox.Disable()
        self.canvas.render(text)

    def on_restart_button(self, event):
        """Handle the event when the user clicks the restart button."""
        text = "Restart button pressed."
        self.monitors_checklistbox.Enable()
        self.continue_button.Disable()
        self.canvas.render(text)
    
    def on_text_box(self, event):
        """Handle the event when the user enters text."""
        text_box_value = self.text_box.GetValue()
        text = "".join(["New text box value: ", text_box_value])
        self.canvas.render(text)

    def on_checkbox(self, event):
        """Handle the event when the user enters text."""
        checkbox_value = self.checkbox.GetValue()
        text = "".join(["New checkbox value: ", str(checkbox_value)])
        self.canvas.render(text)

    def open_circuit_file_in_editor(self, event):
        """
        We set a flag to indicate to logsim that the GUI is to be restarted.
        Then we close the interface and allow logsim to start an editor.
        Afterwards, logsim would restart the GUI.
        """
        self.edit_restart = True
        self.Close()
