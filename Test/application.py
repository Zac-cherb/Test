# coding: utf8
from tkinter import *
from tkinter import ttk
from ttkthemes import ThemedStyle
from tkinter.filedialog import *
from Test import view, annotation


class TabApplication:
    def __init__(self, master, model):

        self.master = master
        self.model = model

        self.nb = ttk.Notebook(self.master, height=800, width=800)
        self.nb.pack(fill=BOTH, expand=YES)

        # Adds tab 1 of the notebook
        self.page1 = ttk.Frame(self.nb)
        self.nb.add(self.page1, text='Viewer')

        # Adds tab 2 of the notebook
        self.page2 = ttk.Frame(self.nb)
        self.nb.add(self.page2, text='Annotation')

        self.annotapp = annotation.AnnotationTab(self.page2, self.model)
        self.viewapp = view.ViewerTab(self.page1, self.model)


class TabApplicationV2:
    def __init__(self, master, model):

        self.master = master
        self.model = model

        self.nb = ttk.Notebook(self.master, height=800, width=800)
        self.nb.pack(fill=BOTH, expand=YES)

        # Adds tab 1 of the notebook
        self.page1 = ttk.Frame(self.nb)
        self.nb.add(self.page1, text='Viewer')

        # Adds tab 2 of the notebook
        self.page2 = ttk.Frame(self.nb)
        self.nb.add(self.page2, text='Annotation')

        self.annotapp = annotation.AnnotationTabV2(self.page2, self.model)
        self.viewapp = view.ViewerTabV2(self.page1, self.model)
