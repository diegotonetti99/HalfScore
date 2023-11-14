import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk
import cairo
import poppler
from PIL import Image
import io


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Things will go here
        self.orientation = self.get_orientation()
        self.set_default_size(600, 800)
        self.set_title("HalfScore")
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.box)
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)

        self.open_dialog = Gtk.FileDialog.new()
        self.open_dialog.set_title("Select a File")

        # Create a menu button
        self.open_button = Gtk.Button()
        self.open_button.connect('clicked', self.show_open_dialog)
        self.open_button.set_icon_name("document-open-symbolic")  # Give it a nice icon

        # Add menu button to the header bar
        self.header.pack_start(self.open_button)

        # drawing areas to display half page
        self.dw_1 = Gtk.DrawingArea()q
        # Make it fill the available space (It will stretch with the window)
        # top
        self.dw_1.set_hexpand(True)
        self.dw_1.set_vexpand(True)
        self.overlay_1 = Gtk.Overlay()
        self.overlay_1.set_child(self.dw_1)
        self.prev_button = Gtk.Button()
        self.prev_button.set_valign(Gtk.Align.FILL)
        self.prev_button.set_halign(Gtk.Align.FILL)
        self.prev_button.connect('clicked', self.prev)
        self.overlay_1.add_overlay(self.prev_button)
        self.box.append(self.overlay_1)
        # separator
        self.separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.box.append(self.separator)
        # bottom
        self.dw_2 = Gtk.DrawingArea()
        self.dw_2.set_hexpand(True)
        self.dw_2.set_vexpand(True)
        self.overlay_2 = Gtk.Overlay()
        self.overlay_2.set_child(self.dw_2)
        self.next_button = Gtk.Button()
        self.next_button.set_valign(Gtk.Align.FILL)
        self.next_button.set_halign(Gtk.Align.FILL)
        self.next_button.connect('clicked', self.next)
        self.overlay_2.add_overlay(self.next_button)
        self.box.append(self.overlay_2)


        # Instead, If we didn't want it to fill the available space but wanted a fixed size
        #self.dw.set_content_width(100)
        #self.dw.set_content_height(100)

    def get_orientation(self):
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        scale_factor = monitor.get_scale_factor()
        geometry = monitor.get_geometry()
        vertical = False
        if geometry.width<geometry.height:
             vertical = True
        

    def draw_1(self, area, context, w, h, data):
        if self.document == None:
            return
        surface, image = self.render(w, self.page_number_1)
        context.set_source_surface(surface, 0, -int(image.height/2)+ h)
        context.paint()
        
    def draw_2(self, area, context, w, h, data):
        if self.document == None:
            return
        surface, image = self.render(w, self.page_number_2)
        context.set_source_surface(surface, 0, -int(image.height/2))
        context.paint()
        
    def render(self, w, n):
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
        #print(f'bytes used per pixel: {len(buf)/(width*height)}')

        surface = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, image.width, image.height)
        return surface, image
  
    def prev(self, button):
        if self.switch:
            self.page_number_2, overlflow = self.decrement(self.page_number_2)
        else:
            self.page_number_1, overlflow = self.decrement(self.page_number_1)
        if not overlflow:
            self.switch = not self.switch
        self.dw_1.queue_draw()
        self.dw_2.queue_draw()

    def decrement(self, n):
        n -=1
        if n<0:
            return 0, True
        return n, False

    def increment(self, n):
        n +=1
        if n>self.document.pages-1:
            return self.document.pages-1, True
        return n, False

    def next(self, button):
        if self.switch:
            self.page_number_2, overflow = self.increment(self.page_number_2)
        else:
            self.page_number_1, overflow = self.increment(self.page_number_1)
        if not overflow:
            self.switch = not self.switch
        self.dw_1.queue_draw()
        self.dw_2.queue_draw()

    def show_open_dialog(self, button):
        self.open_dialog.open(self, None, self.open_dialog_open_callback)
        
    def open_dialog_open_callback(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file is not None:
                # Handle loading file from here
                self.file = file.get_path()
                self.page_number_1 = 0
                self.page_number_2 = 0
                self.switch = False
                self.document = poppler.load_from_file(self.file)
                self.dw_1.set_draw_func(self.draw_1, None)
                self.dw_2.set_draw_func(self.draw_2, None)
        except GLib.Error as error:
            print(f"Error opening file: {error.message}")
     

class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()

app = MyApp(application_id="com.diegotonetti.HalfScore")
app.run(sys.argv)
