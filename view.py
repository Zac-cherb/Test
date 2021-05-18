from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import *
import PIL
from PIL import ImageTk, Image, ImageOps
from PIL.Image import *
from PIL.Image import BOX, LINEAR, NEAREST, EXTENT, fromarray
import numpy

class ResizableCanvas(Canvas):
    """
    A class extending the tkinter Canvas class and enabling resizing
    """
    def __init__(self, parent, **kwargs):
        Canvas.__init__(self, parent, **kwargs)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

    def on_resize(self, event):
        # determine the ratio of old width/height to new width/height
        wscale = float(event.width) / self.width
        hscale = float(event.height) / self.height
        self.width = event.width
        self.height = event.height
        # resize the canvas
        self.config(width=self.width, height=self.height)


class ViewerTab:
    """
    A simple Viewer class
    """
    def __init__(self, master, model, dim=800):

        self.master = master
        self.model = model
        self.image_x_abs = 0.
        self.image_y_abs = 0.
        self.isSlideOn = False
        self.isSuperposed = False
        self.isFISH = False
        self.image = None
        self.cmap = None
        self.photoimage = None
        self.tool = "slide"

        self.xref = 0
        self.yref = 0

        # creation of a frame on the left of the Canvas
        # just to put some buttons and informations
        self.sideFrame = ttk.Frame(self.master, width=100)
        self.sideFrame.pack(side=LEFT, fill=BOTH)

        self.zoomPanel = ttk.LabelFrame(self.sideFrame, width=90,
                                        text="Control Panel")
        self.zoomPanel.pack(side=TOP)

        # creation of a frame on the right of the canvas
        # It will hold the labels for the colormap
        self.rsideFrame = ttk.Frame(self.master, width=100)
        self.rsideFrame.pack(side=RIGHT, fill=BOTH)

        self.labelPanel = ttk.LabelFrame(self.rsideFrame, width=90,
                                                text="Labels")
        self.labelPanel.pack(side=TOP)

        # image container
        self.canvas = ResizableCanvas(self.master,
                                      width=dim,
                                      height=dim,
                                      highlightthickness=0,
                                      bg="black")
        self.canvas.pack(fill=BOTH, expand=YES)

        # canvas bind events
        self.canvas.bind("<Button-1>", self.dirbutton)
        self.canvas.bind("<B1-Motion>", self.move)
        self.canvas.bind("<ButtonRelease-1>", self.nomove)
        self.canvas.bind("<Button-2>", self.get_position)

        self.buttonzoom = ttk.Button(self.zoomPanel, text="Zoom",
                                     command=self.zoom)
        self.buttondezoom = ttk.Button(self.zoomPanel, text="Dezoom",
                                       command=self.dezoom)
        self.buttonrotate = ttk.Button(self.zoomPanel, text="Rotate",
                                       command=self.rotate)
        self.buttonflip = ttk.Button(self.zoomPanel, text="Flip",
                                       command=self.flip)

        self.buttonzoom.pack()
        self.buttondezoom.pack()
        self.buttonrotate.pack()
        self.buttonflip.pack()

        self.vars = []
        self.values = []
        self.buttons = []
        self.label_dict = {}
        self.select_var = IntVar()
        self.select_var.set(1)
        self.buttonselect = Checkbutton(self.labelPanel, text='Select All',
                                        var=self.select_var, onvalue=1,
                                        offvalue=0, command=self.selectall)
        self.buttonselect.pack()

        self.unselect_var = IntVar()
        self.unselect_var.set(0)
        self.buttonunselect = Checkbutton(self.labelPanel, text='Unselect All',
                                        var=self.unselect_var, onvalue=1,
                                        offvalue=0, command=self.unselectall)
        self.buttonunselect.pack()


        self.changelabels = ttk.Button(self.labelPanel, text="Change labels",
                                     command=self.popup_labels)
        self.changelabels.pack()


    def initView(self):
        # done
        """
        A function that create the image in the canvas
        and initialize several variables
        """
        # if there is an image in the canvas, delete it
        self.canvas.delete('all')

        # image creation
        self.image = self.model.initImage()
        self.image.putalpha(255)
        self.model.angle = 0
        self.redraw()
        self.isSlideOn = True

    def initViewSuperposed(self):
        # done
        """
        A function that adds the color map image to the canvas
        """
        # if there is an image in the canvas, delete it
        self.canvas.delete('all')

        # image creation
        self.image = self.model.initImage()
        self.cmap = self.model.initImagePng()
        self.cmap = PIL.Image.fromarray((self.cmap * 255).astype(numpy.uint8))
        self.isSuperposed = True
        self.isSlideOn = True
        self.set_labels()
        self.redrawSuperposed()

    def redraw(self):
        self.image.putalpha(255)
        if self.model.flip:
            self.image = ImageOps.mirror(self.image)
        self.photoimage = ImageTk.PhotoImage(self.image.rotate(self.model.angle))
        self.canvas.delete("image")
        self.canvas.create_image(-self.canvas.width,
                                 -self.canvas.height,
                                 anchor=NW,
                                 image=self.photoimage,
                                 tags="image")
        self.canvas.pack()

    def my_resize(self, size): #Not better than PIL.Image.transform or resize method

        needed_y , needed_x = size
        size_new_image = max([needed_x,needed_y])
        new_image = PIL.Image.new('RGBA',(size_new_image,size_new_image))
        n = numpy.array(new_image)
        factor = (2**self.model.level)
        pixel_size = 1

        for key in self.model.positions.keys():
            if key != 'size_x' and key != 'size_y':
                xo = int( (key[0] *598) / factor)
                yo = int( (key[1] *598) /factor)


            if self.model.level > 7:
                pixel_size = 1

            if self.model.level == 7:
                pixel_size = 4

            if self.model.level == 6:
                pixel_size = 9

            if self.model.level == 5:
                pixel_size = 18

            if self.model.level == 4:
                pixel_size = 37

            if self.model.level == 3:
                pixel_size = 74

            elif self.model.level == 2:
                pixel_size = 149

            elif self.model.level == 1:
                pixel_size = 299

            elif self.model.level == 0:
                pixel_size = 598

            for i in range(pixel_size):
                for j in range(pixel_size):
                    x_good = xo + i
                    y_good = yo + j
                    if x_good > needed_x:
                        x_good = 0
                    if y_good > needed_y:
                        y_good = 0
                    #print("i want ", x_good,y_good)
                    n[x_good,y_good] = self.model.positions[key]

        new_image = PIL.Image.fromarray(n)
        print("cmap size : ",new_image.size,"| slide size :", needed_x,needed_y, "| zoom lvl :", self.model.level, "| pixel size :", pixel_size)
        return new_image

    def redrawSuperposed(self):
        self.image.putalpha(255)
        if self.isFISH:
            n = numpy.array(self.image)
            x, y = numpy.where(n[:, :, 0] > 0)
            #print(x,y)
            min_x = int(min(x))
            min_y = int(min(y))
            max_x = int(max(x))
            max_y = int(max(y))
            dx = max_x - min_x
            dy = max_y - min_y
            size = (dy,dx)
            #print("Size cmap ",self.cmap.size,"Zoom factor ",self.model.level)

            #self.cmap = self.cmap.transform(size,EXTENT,(0,0)+self.cmap.size)
            self.cmap = self.my_resize((dx,dy))
            self.image.paste(self.cmap,(min_y,min_x),self.cmap)
        else:
            self.cmap.putalpha(self.model.tcmap)
            self.cmap_resize = self.cmap.resize(self.model.slide.level_dimensions[self.model.level], resample=NEAREST)
            mod = int(round(self.cmap_resize.size[0]/(self.cmap.size[0]*3)))
            image = self.image.copy()
            image.paste(self.cmap_resize, (self.model.cmapx, self.model.cmapy+mod), mask=self.cmap_resize)
            if self.model.flip:
                image = ImageOps.mirror(image)

        self.photoimage = ImageTk.PhotoImage(image.rotate(self.model.angle))
        self.canvas.delete("image")
        self.canvas.create_image(-self.canvas.width,
                                 -self.canvas.height,
                                 anchor=NW,
                                 image=self.photoimage,
                                 tags="image")
        self.canvas.pack()


    def dirbutton(self, event):
        # done
        if self.isSlideOn:
            if self.tool == "slide":
                self.xref = event.x
                self.yref = event.y

    def move(self, event):
        # done
        if self.isSlideOn:
            if self.tool == "slide":
                dpx = (event.x - self.xref)
                dpy = (event.y - self.yref)
                self.canvas.delete("image")
                self.canvas.create_image(-self.canvas.width + dpx,
                                         -self.canvas.height + dpy, anchor=NW,
                                         image=self.photoimage, tags="image")

    def nomove(self, event):
        # done

        if self.isSuperposed:
            if self.tool == "slide":
                self.image = self.model.translateImage(self.xref,
                                                       self.yref,
                                                       event)
                self.redrawSuperposed()

        if self.isSlideOn and self.isSuperposed == False:
            if self.tool == "slide":
                self.image = self.model.translateImage(self.xref,
                                                       self.yref,
                                                       event)
                self.redraw()

    def zoom(self):
        if self.isSuperposed:
            self.image = self.model.zoomIn()
            self.redrawSuperposed()

        if self.isSlideOn and self.isSuperposed == False:
            # reset level
            self.image = self.model.zoomIn()
            self.redraw()

    def dezoom(self):
        if self.isSuperposed:
            self.image = self.model.zoomOut()
            self.redrawSuperposed()

        if self.isSlideOn and self.isSuperposed == False:
            self.image = self.model.zoomOut()
            self.redraw()

    def rotate(self):
        if self.isSuperposed:
            self.model.angle += 90
            if self.model.angle == 360:
                self.model.angle = 0
            self.redrawSuperposed()

        if self.isSlideOn and self.isSuperposed == False:
            self.model.angle += 90
            self.redraw()

    def flip(self):
        if self.isSuperposed:
            if self.model.flip:
                self.model.flip = False
            else:
                self.model.flip = True
            self.redrawSuperposed()

        if self.isSlideOn and self.isSuperposed == False:
            if self.model.flip:
                self.model.flip = False
            else:
                self.model.flip = True
            self.redraw()

    def get_position(self, event):
        factory = (-1)*int(numpy.sin(numpy.radians(self.model.angle))) + int(numpy.cos(numpy.radians(self.model.angle)))
        factorx = int(numpy.sin(numpy.radians(self.model.angle))) + int(numpy.cos(numpy.radians(self.model.angle)))*(-1)**(self.model.angle/90)
        if self.model.flip:
            event.x = self.canvas.width - event.x
        if self.model.angle % 180 == 0:
            abs_x = factorx*event.x + self.canvas.width*2**(self.model.angle/180) - self.model.cmapx
            abs_y = factory*event.y + self.canvas.height*2**(self.model.angle/180) - self.model.cmapy
        else:
            abs_x = factory*event.y + (3*self.canvas.width+self.canvas.height*(factorx))/2 - self.model.cmapx
            abs_y = factorx*event.x + (3*self.canvas.height+self.canvas.width*(factory))/2 - self.model.cmapy
        factor_resize_x = self.cmap_resize.size[0]/self.model.cmap_png.shape[0]
        factor_resize_y = self.cmap_resize.size[1]/self.model.cmap_png.shape[1]
        index_x = int(abs_x/factor_resize_x)
        index_y = int(abs_y/factor_resize_y)
        messagebox.showinfo('Patch coordinates', 'X: % d \n Y: % d' % (index_x, index_y))

class ViewerTabV2(ViewerTab):

    def __init__(self, master, model, dim=800):

        ViewerTab.__init__(self, master, model, dim)

        # variable for spinbox
        self.spinval = IntVar()
        self.cmap_trans = IntVar()

        # add a slider
        self.thresholdPanel = ttk.LabelFrame(self.sideFrame, width=90,
                                             text="Threshold Panel")
        self.thresholdPanel.pack(side=TOP)
        self.scale = ttk.Scale(master=self.thresholdPanel, command=self.accept_whole_number_only, orient=VERTICAL, from_=51, to=255)
        self.scale.bind("<ButtonRelease-1>", self.update_annotations)
        self.scale.pack(side=LEFT)

        self.threshspinbox = Spinbox(master=self.thresholdPanel, from_=51, to=255, textvariable=self.spinval, command=self.update, width=10)
        self.threshspinbox.pack(side=LEFT)

        # add a slider
        self.CmapTransparency = ttk.LabelFrame(self.sideFrame, width=90,
                                             text="Transparency Cmap")
        self.CmapTransparency.pack(side=TOP)
        self.scale_cmap = ttk.Scale(master=self.CmapTransparency, command=self.accept_whole_number_only_cmap, orient=VERTICAL, from_=0, to=255)
        self.scale_cmap.pack(side=LEFT)

        self.cmapspinbox = Spinbox(master=self.CmapTransparency, from_=0, to=255, textvariable=self.cmap_trans, command=self.update_cmap, width=10)
        self.cmapspinbox.pack(side=LEFT)


    def accept_whole_number_only(self, e=None):
        value = self.scale.get()
        if int(value) != value:
            self.scale.set(round(value))
        self.spinval.set(int(round(value)))
        self.model.thresh = self.spinval.get()

    def update(self, e=None):
        """Updates the scale and spinbox"""
        self.scale.set(self.threshspinbox.get())
        self.model.thresh = self.spinval.get()

    def update_annotations(self, event):
        # can call any function that update annotations in the model
        self.image = self.model.updateImage()
        self.redraw()

    def accept_whole_number_only_cmap(self, e=None):
        value = self.scale_cmap.get()
        if int(value) != value:
            self.scale_cmap.set(round(value))
        #self.cmap_trans.set(int(round(value)))
        #self.model.tcmap = self.cmap_trans.get()
        self.model.tcmap = int(self.scale_cmap.get())
        self.cmap_trans.set(int(self.scale_cmap.get()))
        if self.isSuperposed:
            self.redrawSuperposed()

    def update_cmap(self, e=None):
        """Updates the scale and spinbox"""
        self.scale_cmap.set(self.cmapspinbox.get())
        #self.model.tcmap = self.cmap_trans.get()
        self.model.tcmap = int(self.cmapspinbox.get())

    def change_dict(self):
        n = 0
        temp_dict = {(int(c[0])): (float(c[1]), float(c[2]), float(c[3])) for c in self.model.original_color_dict}
        for i in range(len(self.vars)):
            value = self.vars[i].get()
            if not value:
                temp_dict[self.values[i]] = (0.3216,0.3294,0.6392)
                self.select_var.set(0)
                n += 1
        self.model.color_dict = temp_dict
        image = numpy.array([[self.model.color_dict[x] for x in row] for row in self.model.cmap_png.astype(int)])
        self.cmap = numpy.transpose(image, (1, 0, 2))
        self.cmap = PIL.Image.fromarray((self.cmap * 255).astype(numpy.uint8))
        self.redrawSuperposed()
        if n <= len(self.vars): self.unselect_var.set(0)
        return

    def popup_labels(self):
        top = Toplevel()
        top.title("Dictionary of labels")

        Options = ['Select cluster']
        Options.extend(self.values)
        variable = StringVar()
        variable.set(Options[0])
        msg = Message(top, text='Select class to rename')
        msg.pack()

        w = OptionMenu(top, variable, *Options)
        w.pack()

        msg = Message(top, text='Introduce the name of the new class')
        msg.pack()

        text = Entry(top)
        text.pack()

        button = Button(top, text="Accept", command=lambda: [self.change_label(text.get(), variable.get()), top.destroy()])
        button.pack()

    def change_label(self, name, cluster):
        self.buttons[int(cluster)].config(text='{}: {}'.format(cluster, name))
        self.label_dict[cluster] = name
        return

    def set_labels(self):
        for i in range(self.model.max_cluster + 1):
            value = i
            self.values.append(value)
            var = StringVar(value=value)
            self.vars.append(var)
            colors = self.model.color_dict[i]
            r = int(colors[0]*255)
            g = int(colors[1]*255)
            b = int(colors[2]*255)
            cb = Checkbutton(self.labelPanel, var=var, text=value,
                             onvalue=value, offvalue="",
                             command=lambda: self.change_dict(),
                             bg='#%02x%02x%02x' % (r,g,b))
            cb.pack(side="top", fill="x", anchor="w")
            self.buttons.append(cb)


    def selectall(self):
        for var in self.vars:
            i = self.vars.index(var)
            if not var.get():
                var.set(self.values[i])
        self.change_dict()

    def unselectall(self):
        for var in self.vars:
            var.set("")
        self.change_dict()
