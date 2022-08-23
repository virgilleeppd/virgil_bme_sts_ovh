import numpy as np
from pymongo import MongoClient
import certifi
import collections
from collections import defaultdict
#try:
from sts import getSTSHistogram
from ovh import getOVH
from DataFetcher import DataFetcher
from tqdm import tqdm
from similarity import getOVHEmd,getSTSEmd
    #from similarity_calculation import cal_dissimilarity_ovh,cal_dissimilarity_sts,cal_dissimilarity_td,cal_similarity
#except ImportError: # Used for running notebooks in `similarity` folder
    #import sys
    #sys.path.append('..')
    #from .sts import getSTSHistogram
    #from .ovh import getOVH
    #from .DataFetcher import DataFetcher
    #from .similarity import getOVHEmd,getSTSEmd
from utils import *
connect_mongo=True
local=False
data_fetcher = DataFetcher(connect_mongo=connect_mongo,local=local)
n_bins = 10
patient_id='2212228524'
serverURL="mongodb+srv://mengxuan:lmxcm1234eppd@cluster0.hp9aej0.mongodb.net/?retryWrites=true&w=majority"
client=MongoClient(serverURL,tlsCAFile=certifi.where())
#DBStudy_list=data_fetcher.get_dbstudy_list(patient_id)
def get_study_id(client,patient_name):
  db = client['dicomRt']
  collection=db.studies
  return list(collection.find({"PatientName": patient_name}))[0]['StudyInstanceUID']
def query_for_roi_list(client,study_id):
  db = client['dicomRt']
  collection=db.roi
  return list(collection.find({"Study_ID": study_id}))
def query_for_roi_name(client,refroinos):
  db = client['dicomRt']
  collection = db.roi
  return list(collection.find({"ReferenceROInum":refroinos},{"ROIName": 1}))[0]['ROIName']

def query_for_contour(client,refROInum, SOPInstanceUID):
  db=client['dicomRt']
  collection=db.rtContour
  return list(collection.find({"$and":[{"SOPInstanceUID": SOPInstanceUID},{"ReferenceROInum":refROInum}]}))

def query_for_image_plane_info(client,SOPInstanceUID):
  db=client['dicomRt']
  temp=db.rtStructureSet
  Study_ID=list(temp.find({"SOPInstanceUID": SOPInstanceUID}))[0]['Study_ID']
  collection=db.ctImages
  return list(collection.find({"Study_ID": Study_ID}))

def query_for_image_plane_info_new(client,SOPInstanceUID,ct_position):
  db=client['dicomRt']
  temp=db.rtStructureSet
  Study_ID=list(temp.find({"SOPInstanceUID": SOPInstanceUID}))[0]['Study_ID']
  collection=db.ctImages
  return list(collection.find({"Study_ID": Study_ID,'SliceLocation':ct_position}))

def __get_contours(roi):
    roi_id = roi['ReferenceROInum']

    contour_dict = {}
    imagePatientOrientaion = {}
    imagePatientPosition = {}
    pixelSpacing = {}
    block_shape = []
    Contours = query_for_contour(client, roi['ReferenceROInum'], roi['SOPInstanceUID'])

    for contour in Contours:
        contour_array = np.array(contour['ContourData'], dtype=np.float32)
        contour_array = contour_array.reshape(contour_array.shape[0] // 3, 3)

        contour_dict[contour['_id']] = contour_array
        image_info = query_for_image_plane_info(client, contour['SOPInstanceUID'])[0]
        imagePatientOrientaion[contour['_id']] = np.array(image_info['ImageOrientationPatient'], dtype=np.float32)

        spacing_array = np.array(image_info['PixelSpacing'], dtype=np.float32)
        pixelSpacing[contour['_id']] = spacing_array

        if not block_shape:
            block_shape = (image_info['Rows'], image_info['Columns'])

        imagePatientPosition[contour['_id']] = np.array(image_info['ImagePositionPatient'], dtype=np.float32)

    pixel_spacing = pixelSpacing
    return getContours(block_shape, contour_dict, image_orientation=imagePatientOrientaion,
                       image_position=imagePatientPosition, pixel_spacing=pixelSpacing), imagePatientPosition

def get_contours(patient_id):
    '''
    Get contour block for all rois under this studyID
    we need fetch following things to construct
    block_shape
    slice_position_z
    contour_data
    image_orientation
    image_position
    pixel_spacing
    :param studyID:

    Parameters
    ----------
    StudyID : string
        ID in the new dataset. Typically a single number, e.g. `'1'` or `'2'`.

    Returns
    --------
    ptv_dict : List of Dict
    a list of dictionaries, the first dictionary contains ptv and the second contains PTV
        in the dictionary the key is the name of ROI, the value is the contour block.

    oar_dict : list of Dict
        a list of dictionaries, the first dictionary contains ptv and the second contains OAR
        in the dictionary the key is the name of ROI, the value is the contour block.
    '''
    studyID = get_study_id(client, patient_id)
    rois = query_for_roi_list(client, studyID)
    ptv_dict = {}
    oar_dict = {}

    print("Getting Contours for each ROI")
    for roi in tqdm(rois):
        roi_id = roi['ReferenceROInum']
        contour_block, roi_block = __get_contours(roi)

        # Checks for PTVs using ROI name -> if it contains PTV we assume it is a PTV
        roi_name = query_for_roi_name(client, roi_id)
        roi_interpretation = roi["RTROIInterpretedType"]
        if "PTV" in roi_interpretation or "CTV" in roi_interpretation:
            ptv_dict[roi_name] = (contour_block, roi_block)
        elif "none" in roi_interpretation.lower():
            if "ptv" in roi_name.lower():
                ptv_dict[roi_name] = (contour_block, roi_block)
            else:
                oar_dict[roi_name] = (contour_block, roi_block)
        else:
            oar_dict[roi_name] = (contour_block, roi_block)

    return ptv_dict, oar_dict

#a,b=get_contours(patient_id)
#for item in b:
    #print(item)
    #print(np.count_nonzero(b[item]))
#print(b)
studyID = get_study_id(client, patient_id)
rois = query_for_roi_list(client, studyID)
roi_test=rois[0]
roi_id = roi_test['ReferenceROInum']

contour_dict = {}
imagePatientOrientaion = {}
imagePatientPosition = {}
pixelSpacing = {}
block_shape = []
Contours = query_for_contour(client, roi_test['ReferenceROInum'], roi_test['SOPInstanceUID'])
for contour in Contours:
    contour_array = np.array(contour['ContourData'], dtype=np.float32)
    contour_array = contour_array.reshape(contour_array.shape[0] // 3, 3)

    contour_dict[contour['_id']] = contour_array
    ct_position=contour['ContourData'][2]
    image_info = query_for_image_plane_info_new(client, contour['SOPInstanceUID'],ct_position)[0]
    imagePatientOrientaion[contour['_id']] = np.array(image_info['ImageOrientationPatient'], dtype=np.float32)

    spacing_array = np.array(image_info['PixelSpacing'], dtype=np.float32)
    pixelSpacing[contour['_id']] = spacing_array

    if not block_shape:
        block_shape = (image_info['Rows'], image_info['Columns'])

    imagePatientPosition[contour['_id']] = np.array(image_info['ImagePositionPatient'], dtype=np.float32)

contour_data=contour_dict
image_position=imagePatientPosition
image_orientation=imagePatientOrientaion
pixel_spacing=pixelSpacing


slice_position_z = np.zeros(len(contour_data)).astype(np.float32)
for i, ct in enumerate(image_position.values()):
    slice_position_z[i] = ct[2]
np.sort(slice_position_z)[::-1]

block_shape = block_shape + (len(contour_data),)
contour_block = np.zeros((block_shape)).astype(np.int8)
roi_block = np.zeros((block_shape)).astype(np.int8)

for sop in contour_data:

    z_coor = contour_data[sop][0, 2]

    count = 0
    row_coordinates = np.zeros((contour_data[sop].shape[0])).astype(np.int)
    col_coordinates = np.zeros((contour_data[sop].shape[0])).astype(np.int)
    plane_coor = np.argwhere(slice_position_z == z_coor).astype(np.int)
    for n in range(0, contour_data[sop].shape[0]):
        px = contour_data[sop][n, 0]
        py = contour_data[sop][n, 1]

        xx = image_orientation[sop][0]
        xy = image_orientation[sop][1]
        yx = image_orientation[sop][3]
        yy = image_orientation[sop][4]

        sx = image_position[sop][0]
        sy = image_position[sop][1]

        delJ = pixel_spacing[sop][0]
        delI = pixel_spacing[sop][1]

        A = np.array([[xx * delI, yx * delJ], [xy * delI, yy * delJ]])
        b = np.array([px - sx, py - sy])

        v = np.linalg.solve(A, b)
        col_coordinates[count] = int(np.round(v[0]))
        row_coordinates[count] = int(np.round(v[1]))

        contour_block[row_coordinates[count], col_coordinates[count], plane_coor] = 1

        count += 1

    rr, cc = polygon(row_coordinates, col_coordinates, shape=contour_block.shape[:2])
    roi_block[rr, cc, plane_coor] = 1
numm=np.count_nonzero(roi_block)
print(-1)