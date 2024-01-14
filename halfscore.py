import sys
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gio, Gdk
import cairo
import poppler
#from PIL import Image
import io
import json
import numpy as np

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Things will go here
        #self.orientation = self.get_orientation()
        self.set_default_size(600, 800)
        self.set_title("HalfScore")
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.box)
        # title bar
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)

        # file dialog
        self.open_dialog = Gtk.FileDialog.new()
        self.open_dialog.set_title("Select a File")
        f = Gtk.FileFilter()
        f.set_name("PDF files")
        f.add_pattern("*.pdf")
        filters = Gio.ListStore.new(Gtk.FileFilter)  # Create a ListStore with the type Gtk.FileFilter
        filters.append(f)  # Add the file filter to the ListStore. You could add more.
        self.open_dialog.set_filters(filters)  # Set the filters for the open dialog
        self.open_dialog.set_default_filter(f)
        folder = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_MUSIC)
        self.open_dialog.set_initial_folder(Gio.File.new_for_path(folder))

        # Create a menu button
        self.open_button = Gtk.Button()
        self.open_button.connect('clicked', self.show_open_dialog)
        self.open_button.set_icon_name("document-open-symbolic")  # Give it a nice icon
        self.header.pack_start(self.open_button)
        # Create pen button
        self.pen_button = Gtk.ToggleButton(label="Pen")
        self.header.pack_start(self.pen_button)
        self.pen_button.connect("toggled", self.toggle_pen)
        # Create a color button
        '''self.color = Gdk.RGBA()
        self.color.parse("#0000FF")
        self.color_button = Gtk.ColorButton().new_with_rgba(self.color)
        self.header.pack_start(self.color_button)'''
        # Create a eraser button
        self.eraser_button = Gtk.ToggleButton(label='Eraser')
        self.header.pack_start(self.eraser_button)
        self.eraser_button.connect('toggled', self.toggle_eraser)
        
        # mouse gestures for drawing
        self.strokes_1 = []
        press1 = Gtk.GestureClick.new()
        press1.connect("pressed", self.press1)
        press2 = Gtk.GestureClick.new()
        press2.connect("pressed", self.press2)
        release1 = Gtk.GestureClick.new()
        release1.connect('released', self.release1)
        release2 = Gtk.GestureClick.new()
        release2.connect('released', self.release2)
        motion1 = Gtk.EventControllerMotion.new()
        motion1.connect("motion", self.mouse_motion1)
        motion2 = Gtk.EventControllerMotion.new()
        motion2.connect('motion', self.mouse_motion2)

        self.press_flag = False
        # drawing areas to display half page
        self.dw_1 = Gtk.DrawingArea()
        # Make it fill the available space (It will stretch with the window)
        # top
        self.dw_1.set_hexpand(True)
        self.dw_1.set_vexpand(True)
        self.dw_1.add_controller(press1)
        self.dw_1.add_controller(motion1)
        self.dw_1.add_controller(release1)
        self.overlay_1 = Gtk.Overlay()
        self.overlay_1.set_child(self.dw_1)
        self.prev_button = Gtk.Button()
        self.prev_button.set_valign(Gtk.Align.FILL)
        self.prev_button.set_halign(Gtk.Align.FILL)
        self.prev_button.connect('clicked', self.prev)
        self.prev_button.set_opacity(0.0)
        self.overlay_1.add_overlay(self.prev_button)
        self.box.append(self.overlay_1)

        # bottom
        self.strokes_2 = []

        self.dw_2 = Gtk.DrawingArea()
        self.dw_2.set_hexpand(True)
        self.dw_2.set_vexpand(True)
        self.dw_2.add_controller(press2)
        self.dw_2.add_controller(motion2)
        self.dw_2.add_controller(release2)
        self.overlay_2 = Gtk.Overlay()
        self.overlay_2.set_child(self.dw_2)
        self.next_button = Gtk.Button()
        self.next_button.set_valign(Gtk.Align.FILL)
        self.next_button.set_halign(Gtk.Align.FILL)
        self.next_button.connect('clicked', self.next)
        self.next_button.set_opacity(0.0)
        self.overlay_2.add_overlay(self.next_button)
        self.box.append(self.overlay_2)

    def mouse_motion1(self, motion, x, y):
        if not self.press_flag:
            return
        if self.pen_button.get_active():
            self.stroke.append((x, y))
        elif self.eraser_button.get_active():
            for stroke in self.strokes_1[self.page_number_1]:
                for xs ,ys in stroke:
                    if np.linalg.norm(np.array((x-xs, y-ys))) < 5:
                        self.strokes_1[self.page_number_1].remove(stroke)
        self.dw_1.queue_draw()  # Force a redraw

    def mouse_motion2(self, motion, x, y):
        if not self.press_flag:
            return
        if self.pen_button.get_active():
            self.stroke.append((x, y))
        elif self.eraser_button.get_active():
            for stroke in self.strokes_2[self.page_number_2]:
                for xs ,ys in stroke:
                    if np.linalg.norm(np.array((x-xs, y-ys))) < 5:
                        self.strokes_2[self.page_number_2].remove(stroke)
        self.dw_2.queue_draw()  # Force a redraw

    def save_ink(self):
        file = self.file.replace('.pdf','.json')
        data = {'top': self.strokes_1, 'bottom':self.strokes_2}
        with open(file, "w") as write_file:
            json.dump(data, write_file)

    def press1(self, gesture, data, x, y):
        self.press_flag = True
        if self.pen_button.get_active():
            self.stroke = [(x, y)]
            self.strokes_1[self.page_number_1].append(self.stroke)
    
    def press2(self, gesture, data, x, y):
        self.press_flag = True
        if self.pen_button.get_active():
            self.stroke = [(x, y)]
            self.strokes_2[self.page_number_2].append(self.stroke)

    def release1(self, gesture, data, x, y):
        self.press_flag = False
        self.save_ink()

    def release2(self, gesture, data, x, y):
        self.press_flag = False
        self.save_ink()

    def dw2_click(self, gesture, data, x, y):
        if self.pen_button.get_active():
            self.strokes_2[self.page_number_2].append((x, y))
        elif self.eraser_button.get_active():
            for stroke in self.strokes_2[self.page_number_2]:
                if np.linalg.norm(np.array((x-stroke[0], y-stroke[1]))) < 5:
                    self.strokes_2[self.page_number_2].remove(stroke)
        self.dw_2.queue_draw()  # Force a redraw
        self.save_ink()

    def toggle_pen(self, button):
        if button.get_active():
            self.eraser_button.set_active(False)
        state = not button.get_active()
        self.next_button.set_sensitive(state)
        self.prev_button.set_sensitive(state)
        
    def toggle_eraser(self, button):
        if button.get_active():
            self.pen_button.set_active(False)
        state = not button.get_active()
        self.next_button.set_sensitive(state)
        self.prev_button.set_sensitive(state)
        
    def draw_1(self, area, context, w, h, data):
        '''update top page'''
        if self.document == None:
            return
        surface, image = self.render(w, self.page_number_1)
        context.set_source_surface(surface, 0, -int(image.height/2)+ h)
        context.paint()
        if self.page_number_1 == self.page_number_2:
            context.set_source_rgba(1.0, 1.0, 0.5, 0.15)
        else:
            context.set_source_rgba(1.0, 0.75, 0.5, 0.15)
        context.paint()

        context.set_source_rgba(1.0, 0.0, 0.0, 1.0)
        context.set_line_width(1)
        for stroke in self.strokes_1[self.page_number_1]:
            context.move_to(stroke[0][0], stroke[0][1])
            for x, y in stroke:
                context.line_to(x, y)
            context.stroke()
        
    def draw_2(self, area, context, w, h, data):
        '''update bottom page'''
        if self.document == None:
            return
        surface, image = self.render(w, self.page_number_2)
        context.set_source_surface(surface, 0, -int(image.height/2))
        context.paint()
        if self.page_number_1 == self.page_number_2:
            context.set_source_rgba(1.0, 1.0, 0.5, 0.15)
        else:
            context.set_source_rgba(1.0, 0.75, 0.5, 0.15)
        context.paint()

        context.set_source_rgba(1.0, 0.0, 0.0, 1.0)
        context.set_line_width(1)
        for stroke in self.strokes_2[self.page_number_2]:
            context.move_to(stroke[0][0], stroke[0][1])
            for x, y in stroke:
                context.line_to(x, y)
            context.stroke()

    def render(self, w, n):
        '''render the n-th page of the document with a specified width'''
        renderer = poppler.PageRenderer()
        # Render first page and convert to image buffer
        page = self.document.create_page(n)
        # Use page dimensions to create cairo surface
        rect = page.page_rect()
        width = int(rect.width)
        height = int(rect.height)
        res = int(w/width*72)
        image = renderer.render_page(page, xres=res, yres=res)
        buf = io.BytesIO(image.data).getbuffer()
        surface = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, image.width, image.height)
        return surface, image
  
    def prev(self, button):
        '''load previous half page'''
        if self.page_number_1 > self.page_number_2:
            self.page_number_1, overlflow = self.decrement(self.page_number_1)
        else:
            self.page_number_2, overlflow = self.decrement(self.page_number_2)
        # force page redraw
        self.dw_1.queue_draw()
        self.dw_2.queue_draw()

    def decrement(self, n):
        n -=1
        if n<0:
            # check page overflow
            return 0, True
        return n, False

    def increment(self, n):
        n +=1
        if n>self.document.pages-1:
            # check page overflow
            return self.document.pages-1, True
        return n, False

    def next(self, button):
        '''load next half page'''
        if self.page_number_1 <= self.page_number_2:
            self.page_number_1, overflow = self.increment(self.page_number_1)
        else:
            self.page_number_2, overflow = self.increment(self.page_number_2)
        self.dw_1.queue_draw()
        self.dw_2.queue_draw()

    def show_open_dialog(self, button):
        '''show open file dialog'''
        self.open_dialog.open(self, None, self.open_dialog_open_callback)
        
    def open_dialog_open_callback(self, dialog, result):
        '''load the selected file'''
        try:
            file = dialog.open_finish(result)
            if file is not None:
                # Handle loading file from here
                self.file = file.get_path()
                self.page_number_1 = 0
                self.page_number_2 = 0
                self.document = poppler.load_from_file(self.file)
                self.strokes_1 = [[] for i in range(self.document.pages)]
                self.strokes_2 = [[] for i in range(self.document.pages)]
                jfile = self.file.replace('.pdf','.json')
                try:
                    with open(jfile, 'r') as read_file:
                        data = json.load(read_file)
                        for i in range(self.document.pages):
                            self.strokes_1[i] = data['top'][i]
                            self.strokes_2[i] = data['bottom'][i]
                except:
                    pass
                self.dw_1.set_draw_func(self.draw_1, None)
                self.dw_2.set_draw_func(self.draw_2, None)

        except GLib.Error as error:
            print(f"Error opening file: {error.message}")
     
class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()

app = MyApp(application_id="com.diegotonetti.HalfScore")
app.run(sys.argv)
