# coding: utf8
from skimage.draw import polygon
from skimage.util import view_as_windows
import numpy
from tqdm import tqdm
from tkinter import messagebox
import os
import openslide
from skimage.measure import find_contours, points_in_poly, label
import csv
from skimage.exposure import is_low_contrast
from skimage.morphology import dilation
import pickle


def processBrown2HevClassif(annotations, slide, progressbar):
    if not bool(annotations):
        messagebox.showinfo("Error", "Missing annotations !")
    else:
        from keras.models import load_model
        total = len(annotations.keys())
        print("total number of annotations : ", total)
        cnnpath = os.path.join(os.path.dirname(__file__), 'hev_cnn3.hdf5')
        CNN3 = load_model(cnnpath)
        # progressbar.configure(maximum=total)
        for key in tqdm(annotations.keys()):
            if "tumor" not in key:
                coords = annotations[key]["coords"]
                r = numpy.array([c[1] for c in coords])
                c = numpy.array([c[0] for c in coords])
                rr, cc = polygon(r, c)
                # print("polygon ok")
                annotations[key]["pixarea"] = len(rr)
                size = (int((c.max() - c.min() + 500) / 4), int((r.max() - r.min() + 500) / 4))
                image = slide.read_region(location=(c.min() - 250, r.min() - 250),
                                          level=2,
                                          size=size)
                image = numpy.array(image)[:, :, 0:3]
                # print("image ok, shape: ", image.shape)
                patches = view_as_windows(image, (125, 125, 3), step=25)
                plines = patches.shape[0]
                pcols = patches.shape[1]
                patches = patches.reshape(plines * pcols, 125, 125, 3)
                patches = patches.astype(float)
                patches /= 255.
                # print("patches ok number : ", plines * pcols)
                predictions = CNN3.predict(patches)
                # print("prediction ok")
                k_spe = 0
                k_non_spe = 0
                k_no_mark = 0
                for p in predictions:
                    if p[1] == p.max():
                        k_spe += 1
                    if p[2] == p.max():
                        k_non_spe += 1
                    if p[0] == p.max():
                        k_no_mark += 1
                annotations[key]["patches"] = plines * pcols
                annotations[key]["spe"] = k_spe
                annotations[key]["nospe"] = k_non_spe
                if k_spe > k_non_spe:
                    annotations[key]["class"] = "specific"
                    annotations[key]["color"] = "green"
                else:
                    annotations[key]["class"] = "nonspecific"
                    annotations[key]["color"] = "red"

            # progressbar.step()


def annotateSlideArea(slide):
    """
    The function output brown objects contours
    slide : OpenSlide
    """
    # Load the image at pyramid level 4 in memory
    image = slide.read_region(location=(0, 0), level=4,
                              size=slide.level_dimensions[4])
    image = numpy.asarray(image)[:, :, 0:3]
    brown = image[:, :, 0].astype(float) / (1. + image[:, :, 2].astype(float))
    brown = brown > 1.03

    # free some memory before continue
    # del image

    contours = find_contours(brown, 0.2)

    final = dict()

    for k in range(len(contours)):
        imin = int(contours[k][:, 0].min())
        jmin = int(contours[k][:, 1].min())
        imax = int(contours[k][:, 0].max())
        jmax = int(contours[k][:, 1].max())
        if not is_low_contrast(image[imin:imax, jmin:jmax, :]):
            final["brown_" + str(k + 1)] = {'coords': [(int(c[1]) * (2 ** 4), int(c[0]) * (2 ** 4)) for c in contours[k]], 'color': "magenta", 'id': k + 1}

    return final


def csv2dict(csvfile):
    dico = {}
    current_key = None
    with open(csvfile, "r") as f:
        reader = csv.reader(f)
        for line in reader:
            if line:
                if "#" in line[0]:
                    k = 0
                    while line[0] + "_" + str(k) in dico.keys():
                        k += 1
                    current_key = line[0] + "_" + str(k)
                    dico[current_key] = []
                else:
                    dico[current_key].append(tuple([float(l) for l in line]))
    return dico


def csv2annotationfile(csvfile, slide, annotationfilepath):

    # slide definition and properties
    #################################
    mppx = float(slide.properties[openslide.PROPERTY_NAME_MPP_X])
    mppy = float(slide.properties[openslide.PROPERTY_NAME_MPP_Y])
    #############################################################

    annotations = dict()

    dico = csv2dict(csvfile)
    k = 0
    for key in dico.keys():
        if 'Area' not in key:
            k += 1
            annotations[key] = {'coords': [(int(c[0] / mppx) - 9800, int(c[1] / mppy) - 163800) for c in dico[key]], 'color': 'green2', 'id': k}
    with open(annotationfilepath, "wb") as f:
        pickle.dump(annotations, f)


def merge_annotation_files(annotationfilepath1, annotationfilepath2, outputfile, color='red'):
    """
    A function to merge two annotation files.
    It takes the two dictionaries, and merge them.
    A new dictionary is created with element of both dictionaries.
    Keys and Ids are changed but remain unique.
    Annotation 1 keeps its color, but annotation2 take the specified color.
    """

    # open dictionaries in their pickle files
    with open(annotationfilepath1, "rb") as f1:
        annotation1 = pickle.load(f1)

    with open(annotationfilepath2, "rb") as f2:
        annotation2 = pickle.load(f2)

    merge = dict()
    # new keys to insure both id and keys of new dico will be unique
    mergekey = 1

    # loop over first dictionary:
    for key, val in annotation1.items():
        merge[mergekey] = val
        merge[mergekey]['id'] = mergekey
        mergekey += 1

    # loop over second dictionary:
    for key, val in annotation2.items():
        merge[mergekey] = val
        merge[mergekey]['id'] = mergekey
        merge[mergekey]['color'] = color
        mergekey += 1

    with open(outputfile, 'wb') as f3:
        pickle.dump(merge, f3)


def processCsvTumorArea2Brown(annotations, slide, progressbar):
    csvpath = slide._filename
    csvpath = csvpath.split(".")[0] + ".csv"
    if not os.path.exists(csvpath):
        messagebox.showinfo("Error", "No csv annotation file !")
    else:
        # slide definition and properties
        #################################
        mppx = float(slide.properties[openslide.PROPERTY_NAME_MPP_X])
        mppy = float(slide.properties[openslide.PROPERTY_NAME_MPP_Y])
        #############################################################

        # compute contours of brown objects
        ###################################
        brownobjects = annotateSlideArea(slide)
        ##################################

        # compute contours of tumor annotation from csv file
        ####################################################
        annotation = csv2dict(csvpath)

        areakey = None
        for k in annotation.keys():
            if "# Area" in k:
                areakey = k

        if areakey is not None:
            tumorobject = {'coords': [(int(c[0] / mppx) - 9800, int(c[1] / mppy) - 163800) for c in annotation[areakey]], 'color': "green2", 'id': 0}
        ###################################################################################################################################

        # place tumor annotation in polygon data structure
        ##################################################
        tumorpoly = numpy.array([numpy.array(p) for p in tumorobject["coords"]])
        ############################################################

        # find brown objects outside of tumor annotation
        ################################################
        outside = []
        for key in tqdm(brownobjects.keys()):
            points = brownobjects[key]["coords"]
            ppoints = numpy.array([numpy.array(p) for p in points])
            if not points_in_poly(ppoints, tumorpoly).any():
                outside.append(key)
        ###########################

        # remove outside brown objects and store everything
        ###################################################

        for key in brownobjects.keys():
            if key not in outside:
                annotations[key] = brownobjects[key]

        annotations["tumor"] = tumorobject
        ###################################
