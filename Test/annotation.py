
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import *
from PIL import ImageTk
from Test import view


class AnnotationTab:
    def __init__(self, master, model):

        self.master = master
        self.model = model
        self.isannotation = False
        self.image = None
        self.photoimage = None

        # annotation pannel
        self.annotationPannel = ttk.Frame(self.master, width=200)
        self.annotationPannel.pack(side=LEFT, fill=Y)

        # annotation labeled pannel (inside annotation pannel)
        self.annotationSubPannel = ttk.LabelFrame(self.annotationPannel,
                                                  width=190,
                                                  text="Annotation Browser")
        self.annotationSubPannel.pack(side=TOP, fill=BOTH, expand=YES)
        self.maskProposal = ttk.Combobox(self.annotationSubPannel)
        self.maskProposal.bind('<<ComboboxSelected>>', self.maskAnnotation)
        self.maskProposal.pack(side=TOP, fill=X)

        # scrollable annotation list (inside annotation labeled pannel)
        self.scrollannotations = ttk.Scrollbar(self.annotationSubPannel)
        self.annotationList = Listbox(self.annotationSubPannel, bg="gray25")
        self.annotationList.bind("<<ListboxSelect>>", self.checkAnnotation)
        self.scrollannotations.config(command=self.annotationList.yview)
        self.annotationList.pack(side=LEFT, fill=BOTH, expand=YES)

        # individual annotation pannel
        self.individualPannel = ttk.Frame(self.master, width=600)
        self.individualPannel.pack(side=LEFT, fill=BOTH, expand=YES)

        # annotation rough description pannel
        self.descriptionPannel = ttk.LabelFrame(self.individualPannel,
                                                width=200,
                                                text="Annotation Description")
        self.descriptionPannel.pack(side=LEFT, fill=Y)
        self.propertyList = Listbox(self.descriptionPannel, bg="gray25")
        self.propertyList.pack(side=TOP, fill=BOTH, expand=YES)

        # annotation thumbnail
        self.patchPannel = ttk.Frame(self.individualPannel)
        self.patchPannel.pack(side=LEFT, fill=BOTH, expand=YES)
        # future "transform pannel" at the bottom
        self.processPannel = ttk.LabelFrame(self.patchPannel,
                                            height=400,
                                            text="Processes")
        self.processPannel.pack(side=BOTTOM, fill=X, expand=YES)

        self.processButtonPannel = ttk.Frame(self.processPannel, height=50)
        self.processButtonPannel.pack(side=BOTTOM, fill=X, expand=YES)

        self.processButton = ttk.Button(self.processButtonPannel,
                                        text="Process",
                                        command=self.runProcess)
        self.processButton.pack()

        self.progressBar = ttk.Progressbar(self.processPannel)
        self.progressBar.pack(side=BOTTOM, fill=X, expand=YES)

        self.processList = Listbox(self.processPannel, bg="gray25")
        self.processList.pack(side=TOP, fill=BOTH, expand=YES)
        # viewer is a pretty bad idea or I'll have to modify it deeply
        self.patchView = view.ResizableCanvas(self.patchPannel,
                                              bg="black",
                                              highlightthickness=0)
        self.patchView.pack(side=TOP, fill=BOTH, expand=YES)

    def initAnnot(self):
        self.annotationList.delete(0, END)
        namesNcolors = self.model.annotationNames()
        for name in namesNcolors:
            self.annotationList.insert(END, name["name"])
            self.annotationList.itemconfig(END, foreground=name["color"])
        properties = self.model.annotationUniqueProperties()
        properties.append("All")
        self.maskProposal["values"] = properties

        self.processList.delete(0, END)
        processes = self.model.findProcesses()
        for p in processes:
            self.processList.insert(END, p)

    def checkAnnotation(self, evt):
        if self.isannotation:
            w = evt.widget
            index = int(w.curselection()[0])
            color = self.annotationList.itemcget(index, "foreground")
            value = w.get(index)
            detail = self.model.detailedAnnotation(value)
            self.propertyList.delete(0, END)
            for d in detail:
                self.propertyList.insert(END, d)
            bbx, self.image = self.model.imageAnnotation(value)
            self.image.putalpha(255)
            self.photoimage = ImageTk.PhotoImage(self.image)
            self.patchView.delete("all")
            self.patchView.create_image(0,
                                        0,
                                        anchor=NW,
                                        image=self.photoimage,
                                        tags="image")
            self.patchView.create_rectangle(bbx[0], bbx[1], bbx[2], bbx[3], outline=color)
            self.patchView.pack()

    def maskAnnotation(self, evt):
        val = self.maskProposal.get()
        if val == "All":
            self.initAnnot()
        else:
            namesNcolors = self.model.annotationNamesByPropertyVal(val)
            self.annotationList.delete(0, END)
            for name in namesNcolors:
                self.annotationList.insert(END, name["name"])
                self.annotationList.itemconfig(END, foreground=name["color"])

    def runProcess(self):
        if self.processList.get(ACTIVE):
            self.model.runProcess(self.processList.get(ACTIVE),
                                  self.progressBar)
        self.initAnnot()


class AnnotationTabV2:
    def __init__(self, master, model):

        self.master = master
        self.model = model
        self.isfileannotation = False
        self.isannotation = False
        self.image = None
        self.photoimage = None

        # file annotation panel
        self.fileAnnotationPannel = ttk.Frame(self.master, width=200)
        self.fileAnnotationPannel.pack(side=LEFT, fill=Y)

        # file annotation labeled pannel (inside annotation pannel)
        self.fileAnnotationSubPannel = ttk.LabelFrame(self.fileAnnotationPannel,
                                                      width=190,
                                                      text="Annotation Files")
        self.fileAnnotationSubPannel.pack(side=TOP, fill=BOTH, expand=YES)

        # add new annotation file button
        self.buttonAddAnnotationFile = ttk.Button(self.fileAnnotationSubPannel,
                                                  text="Add File",
                                                  command=self.addAnnotationFile)
        self.buttonAddAnnotationFile.pack()

        # add remove annotation file button
        self.buttonRemoveAnnotationFile = ttk.Button(self.fileAnnotationSubPannel,
                                                     text="Remove File",
                                                     command=self.removeAnnotationFile)
        self.buttonRemoveAnnotationFile.pack()

        # scrollable file annotation list (inside file annotation labeled pannel)
        self.scrollannotationfiles = ttk.Scrollbar(self.fileAnnotationSubPannel)
        self.annotationFileList = Listbox(self.fileAnnotationSubPannel, bg="gray25")
        self.annotationFileList.bind("<<ListboxSelect>>", self.checkAnnotationFile)
        self.scrollannotationfiles.config(command=self.annotationFileList.yview)
        self.annotationFileList.pack(side=LEFT, fill=BOTH, expand=YES)

        # annotation pannel
        self.annotationPannel = ttk.Frame(self.master, width=200)
        self.annotationPannel.pack(side=LEFT, fill=Y)

        # annotation labeled pannel (inside annotation pannel)
        self.annotationSubPannel = ttk.LabelFrame(self.annotationPannel,
                                                  width=190,
                                                  text="Annotation Browser")
        self.annotationSubPannel.pack(side=TOP, fill=BOTH, expand=YES)
        self.maskProposal = ttk.Combobox(self.annotationSubPannel)
        self.maskProposal.bind('<<ComboboxSelected>>', self.maskAnnotation)
        self.maskProposal.pack(side=TOP, fill=X)

        # scrollable annotation list (inside annotation labeled pannel)
        self.scrollannotations = ttk.Scrollbar(self.annotationSubPannel)
        self.annotationList = Listbox(self.annotationSubPannel, bg="gray25")
        self.annotationList.bind("<<ListboxSelect>>", self.checkAnnotation)
        self.scrollannotations.config(command=self.annotationList.yview)
        self.annotationList.pack(side=LEFT, fill=BOTH, expand=YES)

        # individual annotation pannel
        self.individualPannel = ttk.Frame(self.master, width=600)
        self.individualPannel.pack(side=LEFT, fill=BOTH, expand=YES)

        # annotation rough description pannel
        self.descriptionPannel = ttk.LabelFrame(self.individualPannel,
                                                width=200,
                                                text="Annotation Description")
        self.descriptionPannel.pack(side=LEFT, fill=Y)
        self.propertyList = Listbox(self.descriptionPannel, bg="gray25")
        self.propertyList.pack(side=TOP, fill=BOTH, expand=YES)

        # annotation thumbnail
        self.patchPannel = ttk.Frame(self.individualPannel)
        self.patchPannel.pack(side=LEFT, fill=BOTH, expand=YES)
        # future "transform pannel" at the bottom
        self.processPannel = ttk.LabelFrame(self.patchPannel,
                                            height=400,
                                            text="Processes")
        self.processPannel.pack(side=BOTTOM, fill=X, expand=YES)

        self.processButtonPannel = ttk.Frame(self.processPannel, height=50)
        self.processButtonPannel.pack(side=BOTTOM, fill=X, expand=YES)

        self.processButton = ttk.Button(self.processButtonPannel,
                                        text="Process",
                                        command=self.runProcess)
        self.processButton.pack()

        self.progressBar = ttk.Progressbar(self.processPannel)
        self.progressBar.pack(side=BOTTOM, fill=X, expand=YES)

        self.processList = Listbox(self.processPannel, bg="gray25")
        self.processList.pack(side=TOP, fill=BOTH, expand=YES)
        # viewer is a pretty bad idea or I'll have to modify it deeply
        self.patchView = view.ResizableCanvas(self.patchPannel,
                                              bg="black",
                                              highlightthickness=0)
        self.patchView.pack(side=TOP, fill=BOTH, expand=YES)

    def initAnnot(self):
        self.annotationList.delete(0, END)
        namesNcolors = self.model.annotationNames()
        for name in namesNcolors:
            self.annotationList.insert(END, name["name"])
            self.annotationList.itemconfig(END, foreground=name["color"])
        properties = self.model.annotationUniqueProperties()
        properties.append("All")
        self.maskProposal["values"] = properties

        self.processList.delete(0, END)
        processes = self.model.findProcesses()
        for p in processes:
            self.processList.insert(END, p)

    def checkAnnotationFile(self, evt):
        self.propertyList.delete(0, END)
        w = evt.widget
        index = int(w.curselection()[0])
        filename = w.get(index)
        if filename:
            self.model.open_annotation_files(filename)
            self.isfileannotation = True
            if '.annot' in filename:
                self.initAnnot()

    def addAnnotationFile(self):
        filename = askopenfilename(title='open annotation file',
                                   filetypes=[('annot files', '.annot'),
                                              ('tif files', '.tif'),
                                              ('tiff files', '.tiff'),
                                              ('png files', '.png')])
        if filename:
            self.model.open_annotation_files(filename)
            self.annotationFileList.insert(END, filename)
            self.isfileannotation = True

    def removeAnnotationFile(self):
        index = int(self.annotationFileList.curselection()[0])
        self.propertyList.delete(0, END)
        self.annotationList.delete(0, END)
        self.annotationFileList.delete(index)

    def checkAnnotation(self, evt):
        if self.isannotation:
            w = evt.widget
            index = int(w.curselection()[0])
            color = self.annotationList.itemcget(index, "foreground")
            value = w.get(index)
            detail = self.model.detailedAnnotation(value)
            self.propertyList.delete(0, END)
            for d in detail:
                self.propertyList.insert(END, d)
            bbx, self.image = self.model.imageAnnotation(value)
            self.image.putalpha(255)
            self.photoimage = ImageTk.PhotoImage(self.image)
            self.patchView.delete("all")
            self.patchView.create_image(0,
                                        0,
                                        anchor=NW,
                                        image=self.photoimage,
                                        tags="image")
            self.patchView.create_rectangle(bbx[0], bbx[1], bbx[2], bbx[3], outline=color)
            self.patchView.pack()

    def maskAnnotation(self, evt):
        val = self.maskProposal.get()
        if val == "All":
            self.initAnnot()
        else:
            namesNcolors = self.model.annotationNamesByPropertyVal(val)
            self.annotationList.delete(0, END)
            for name in namesNcolors:
                self.annotationList.insert(END, name["name"])
                self.annotationList.itemconfig(END, foreground=name["color"])

    def runProcess(self):
        if self.processList.get(ACTIVE):
            self.model.runProcess(self.processList.get(ACTIVE),
                                  self.progressBar)
        self.initAnnot()
