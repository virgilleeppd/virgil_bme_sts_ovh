import numpy as np
import pandas as pd
import pydicom
from pydicom.datadict import keyword_for_tag, tag_for_keyword
import os
import pandas as pd
from pymongo import MongoClient
from tqdm import tqdm
import certifi
global serverURL
parent_path="/Users/virgil_lee/Desktop/Internship/BMEProject/try_code/data/" #Download from https://drive.google.com/drive/folders/1C19w0K-2B6bE4D4VTTJmaqrXZScS0E70?usp=sharing

import json
with open("./DBconfig.json",'r') as fp: 
    config_json=json.load(fp)

def len_sequence(dcm_seq):
    cnt=0
    len1=0
    try:
        while True:
            dcm_seq.value[cnt]#[0][(0x3006,0x002A)
            cnt+=1
    except:
        len1=cnt
    return len1

def parse_dicom(data_path):
    global data
    ls=[i for i in os.listdir(data_path)]
    
    CT_dcm_path=""
    for i in ls:
        if i[:2]=="CT":
            CT_dcm_path+=i
            break
    RT_dcm_path=""
    for i in ls:
        if i[:2]=="RS":
            RT_dcm_path+=i
            break
    patient_id=None
    study_id=None
    series_id=None
    for table in ['patients', 'studies', 'series', 'ctImages']:
        if table == "ctImages":
          for path_temp in os.listdir(data_path):
            if path_temp[:2]=="CT":
                dcm=pydicom.read_file(data_path+path_temp)
                data_temp={}
                for key in config_json[table]:
                    key_ind=[hex(int(i,16)) for i in config_json[table][key].split(',')]
                    if key == "StudyInstanceUID":
                      study_id=str(dcm[key_ind].value)
                    if key == "SeriesInstanceUID":
                      series_id=str(dcm[key_ind].value)
                    if key=="PatientName":
                      patient_id==str(dcm[key_ind].value)
                    try:

                        if type(dcm[key_ind].value) == pydicom.multival.MultiValue:
                            data_temp[key]=list(dcm[key_ind].value)
                        elif type(dcm[key_ind].value) == pydicom.valuerep.DSfloat:
                            data_temp[key]=float(dcm[key_ind].value)
                        elif type(dcm[key_ind].value) in [pydicom.valuerep.PersonName,pydicom.uid.UID]:
                            data_temp[key]=str(dcm[key_ind].value)
                        elif type(dcm[key_ind].value) == pydicom.valuerep.IS:
                            data_temp[key]=int(dcm[key_ind].value)
                        elif type(dcm[key_ind].value) == pydicom.uid.UID:
                            data_temp[key]=str(dcm[key_ind].value)
                        else:
                            data_temp[key]=dcm[key_ind].value    
                    except:
                        data_temp[key]=None
                if table=="ctImages":
                  data_temp['Study_ID']=study_id
                  data_temp['Series_ID']=series_id
                data[table].append(data_temp)
        
        else:

              dcm=pydicom.read_file(data_path+CT_dcm_path)
              data_temp={}
              for key in config_json[table]:
                  key_ind=[hex(int(i,16)) for i in config_json[table][key].split(',')]
                  if key == "StudyInstanceUID":
                    study_id=str(dcm[key_ind].value)
                  if key == "SeriesInstanceUID":
                    series_id=str(dcm[key_ind].value)
                  if key=="PatientName":
                    patient_id==str(dcm[key_ind].value)
                  try:

                      if type(dcm[key_ind].value) == pydicom.multival.MultiValue:
                          data_temp[key]=list(dcm[key_ind].value)
                      elif type(dcm[key_ind].value) == pydicom.valuerep.DSfloat:
                          data_temp[key]=float(dcm[key_ind].value)
                      elif type(dcm[key_ind].value) in [pydicom.valuerep.PersonName,pydicom.uid.UID]:
                          data_temp[key]=str(dcm[key_ind].value)
                      elif type(dcm[key_ind].value) == pydicom.valuerep.IS:
                          data_temp[key]=int(dcm[key_ind].value)
                      elif type(dcm[key_ind].value) == pydicom.uid.UID:
                          data_temp[key]=str(dcm[key_ind].value)
                      else:
                          data_temp[key]=dcm[key_ind].value    
                  except:
                      data_temp[key]=None
              if table=="series":
                data_temp['Study_ID']=study_id
              data[table].append(data_temp)

    dcm=pydicom.read_file(data_path+RT_dcm_path)
    table="rtStructureSet"
    data_temp={}
    for key in config_json[table]:
        key_ind=[hex(int(i,16)) for i in config_json[table][key].split(',')]
        try:
            if type(dcm[key_ind].value) == pydicom.multival.MultiValue:
                data_temp[key]=list(dcm[key_ind].value)
            elif type(dcm[key_ind].value) == pydicom.valuerep.DSfloat:
                data_temp[key]=float(dcm[key_ind].value)
            elif type(dcm[key_ind].value) in [pydicom.valuerep.PersonName,pydicom.uid.UID]:
                data_temp[key]=str(dcm[key_ind].value)
            elif type(dcm[key_ind].value) == pydicom.valuerep.IS:
                data_temp[key]=int(dcm[key_ind].value)
            elif type(dcm[key_ind].value) == pydicom.uid.UID:
                data_temp[key]=str(dcm[key_ind].value)
            else:
                data_temp[key]=dcm[key_ind].value
        except:
            data_temp[key]=None
    data_temp['Study_ID']=study_id
    data_temp['Series_ID']=series_id
    data[table].append(data_temp)

    table="roi"
    roi_name_dict={}
    roi_color_dict={}
    roi_type_dict={}
    try:
        key1=[hex(int(i,16)) for i in config_json[table]['ROIName'].split(',')]
        for i in range(len_sequence(dcm[(0x3006,0x0020)])):
            roi_name_dict[dcm[(0x3006,0x0020)].value[i][(0x3006,0x0022)].value]=str(dcm[(0x3006,0x0020)].value[i][key1].value)

        key2=[hex(int(i,16)) for i in config_json[table]['ROIDisplayColor'].split(',')]
        for i in range(len_sequence(dcm[(0x3006,0x0039)])):
            roi_color_dict[dcm[(0x3006,0x0039)].value[i][(0x3006,0x0084)].value]=list(dcm[(0x3006,0x0039)].value[i][key2].value)

        key3=[hex(int(i,16)) for i in config_json[table]['RTROIInterpretedType'].split(',')]
        for i in range(len_sequence(dcm[(0x3006,0x0080)])):
            roi_type_dict[dcm[(0x3006,0x0080)].value[i][(0x3006,0x0084)].value]=str(dcm[(0x3006,0x0080)].value[i][key3].value)

        for it in roi_name_dict:
            roi_id=None

            data_temp={}
            key_ind=[hex(int(i,16)) for i in config_json[table]['SOPInstanceUID'].split(',')]
            try:
                data_temp['SOPInstanceUID']=str(dcm[key_ind].value)
                data_temp["ReferenceROInum"]=str(it)
                roi_id=str(it)
                data_temp['ROIName']=roi_name_dict[it]
                data_temp['ROIDisplayColor']=roi_color_dict[it]
                data_temp['RTROIInterpretedType']=roi_type_dict[it]
            except:
                data_temp['SOPInstanceUID']=None
                data_temp["ReferenceROInum"]=None
                data_temp['ROIName']=None
                data_temp['ROIDisplayColor']=None
                data_temp['RTROIInterpretedType']=None
            data_temp['Study_ID']=study_id
            data_temp['Series_ID']=series_id
            data[table].append(data_temp)
    except:
        data_temp={}
        for key in config_json[table]:
            key_ind=[hex(int(i,16)) for i in config_json[table][key].split(',')]
            try:
                if type(dcm[key_ind].value) == pydicom.multival.MultiValue:
                    data_temp[key]=list(dcm[key_ind].value)
                elif type(dcm[key_ind].value) == pydicom.valuerep.DSfloat:
                    data_temp[key]=float(dcm[key_ind].value)
                elif type(dcm[key_ind].value) in [pydicom.valuerep.PersonName,pydicom.uid.UID]:
                    data_temp[key]=str(dcm[key_ind].value)
                elif type(dcm[key_ind].value) == pydicom.valuerep.IS:
                    data_temp[key]=int(dcm[key_ind].value)
                elif type(dcm[key_ind].value) == pydicom.uid.UID:
                    data_temp[key]=str(dcm[key_ind].value)
                else:
                    data_temp[key]=dcm[key_ind].value
            except:
                data_temp[key]=None
            data[table].append(data_temp)
    table="rtContour"
    parent=dcm[[0x3006,0x0039]]
    try:
        
        for x in range(len_sequence(parent)):
            sub_parent=parent.value[x]['0x3006','0x0040']
            for i in range(len_sequence(sub_parent)):
                data_temp={}
                try:
                    data_temp['SOPInstanceUID']=str(dcm[[0x0008,0x0018]].value)
                    data_temp["ReferenceROInum"]=str(parent.value[x]['0x3006','0x0084'].value)
                    data_temp["ContourGeometricType"]=str(sub_parent.value[i][[hex(int(i,16)) for i in config_json[table]["ContourGeometricType"].split(',')]].value)
                    data_temp["NumberOfContourPoints"]=str(sub_parent.value[i][[hex(int(i,16)) for i in config_json[table]["NumberOfContourPoints"].split(',')]].value)
                    data_temp["ContourData"]=list(sub_parent.value[i][[hex(int(i,16)) for i in config_json[table]["ContourData"].split(',')]].value)
                    data_temp["ReferencedSOPClassUID"]=str(sub_parent.value[i][[hex(int(i,16)) for i in config_json[table]["ContourImageSequence"].split(',')]].value[0][[hex(int(i,16)) for i in config_json[table]["ReferencedSOPClassUID"].split(',')]].value)
                    data_temp["ReferencedSOPInstanceUID"]=str(sub_parent.value[i][[hex(int(i,16)) for i in config_json[table]["ContourImageSequence"].split(',')]].value[0][[hex(int(i,16)) for i in config_json[table]["ReferencedSOPInstanceUID"].split(',')]].value)
                except:
                    data_temp['SOPInstanceUID']=None
                    data_temp["ReferenceROInum"]=None
                    data_temp["ContourGeometricType"]=None
                    data_temp["NumberOfContourPoints"]=None
                    data_temp["ContourData"]=None
                    data_temp["ReferencedSOPClassUID"]=None
                    data_temp["ReferencedSOPInstanceUID"]=None
                data[table].append(data_temp)
    except:
        data_temp={}
        for key in config_json[table]:
            key_ind=[hex(int(i,16)) for i in config_json[table][key].split(',')]
            try:
                if type(dcm[key_ind].value) == pydicom.multival.MultiValue:
                    data_temp[key]=list(dcm[key_ind].value)
                elif type(dcm[key_ind].value) == pydicom.valuerep.DSfloat:
                    data_temp[key]=float(dcm[key_ind].value)
                elif type(dcm[key_ind].value) in [pydicom.valuerep.PersonName,pydicom.uid.UID]:
                    data_temp[key]=str(dcm[key_ind].value)
                elif type(dcm[key_ind].value) == pydicom.valuerep.IS:
                    data_temp[key]=int(dcm[key_ind].value)
                elif type(dcm[key_ind].value) == pydicom.uid.UID:
                    data_temp[key]=str(dcm[key_ind].value)
                else:
                    data_temp[key]=dcm[key_ind].value
            except:
                data_temp[key]=None
        data[table].append(data_temp)
    return data

def visualizeTables(data):
    for it in data:
        print("Table - ",it)
        df=pd.DataFrame.from_dict(data[it])
        display(df)
        print()

        
def connectMongo():
    cluster = 'mongodb+srv://mengxuan:lmxcm1234eppd@cluster0.hp9aej0.mongodb.net/?retryWrites=true&w=majority'
    client = MongoClient(cluster, tlsCAFile=certifi.where())
    return client
    
def pushToMongo(data):
    client=connectMongo()
    db=client['dicomRt']
    for table in tqdm(list(data.keys())):
        collection = db[table]
        collection.insert_many(data[table])
        print('Collection',table,'Updated')

def iterate_fols(path):
    ls=[i for i in os.listdir(path) if "." not in i]
    for i in tqdm(ls):

            print("Processing Data Folder - ",i)
            dicom_data=parse_dicom(path+i+'//')
            f=open('Log_'+str(i)+'.json','w')
            try:
                f.write(json.dumps(data,indent=5))
                f.close()
            except:
                return data

    pushToMongo(data)
    return data

global data
data={}
for it in config_json:
    data[it]=[]
result=iterate_fols(parent_path)
print('Mongo Upload Successfull!')
print(list(data.keys()))
