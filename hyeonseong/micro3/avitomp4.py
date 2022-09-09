# from crypt import methods
from ast import parse
from flask import Flask, render_template, request, current_app
from werkzeug.utils import secure_filename

import os
import os.path
import shutil
from pymongo import MongoClient
import pymongo
import datetime
import sys
sys.path.append('../hslib')
sys.path.append('../hsdef')
import hsdef as hsdef
import hslib as hslib
from moviepy.editor import *
import time
import requests
from requests.adapters import HTTPAdapter, Retry

client = MongoClient(hsdef.MONGODB_URI,hsdef.MONGODB_PORT)
hs_movie=client[hsdef.CURRENT_DB]
hsm_requests=hs_movie[hsdef.CURRENT_COLLECTION]

def AVI2MP4():
    # find avi(UNAVAIL)
    eq_hs_query={"STATUS":hsdef.ENQUEUE}
    eq_hs_doc=hsm_requests.find(eq_hs_query)
    for q in eq_hs_doc:
        availableFlag=q["FILENAME"][-3:] # mp4인지 avi인지 확인
        if availableFlag=="mp4":
            # q["STATUS"]=hsdef.NO_NEED_CONVERT
            hs_movie.hsm_requests.update_one({"_id":q["_id"]},{"$set":{"STATUS":hsdef.NO_NEED_CONVERT}})
            # q["AVITOMP4_START_TIME"]="NOT AVI"
            hs_movie.hsm_requests.update_one({"_id":q["_id"]},{"$set":{"AVITOMP4_START_TIME":"NOT AVI"}})
            # q["AVITOMP4_END_TIME"]="NOT AVI"
            hs_movie.hsm_requests.update_one({"_id":q["_id"]},{"$set":{"AVITOMP4_END_TIME":"NOT AVI"}})
        else:
            # q["STATUS"]=hsdef.NEED_CONVERT
            hs_movie.hsm_requests.update_one({"_id":q["_id"]},{"$set":{"STATUS":hsdef.NEED_CONVERT}})
            
    
    cv_hs_query={"STATUS":hsdef.NEED_CONVERT}
    cv_hs_doc=hsm_requests.find(cv_hs_query)
    for q in cv_hs_doc:
        filename=q["FILENAME"] #avi
        R_id=str(q["_id"])
        print(1)
        firsturi=os.path.join("http://129.254.202.111:30111","requestids",R_id,"statuses",hsdef.NEED_CONVERT)
        r=requests.put(firsturi)
        print(r)
        time.sleep(5)
        avi_file_path=os.path.join(hsdef.MOVIE_DIR,R_id,hsdef.SRC,filename) #avi path
        output_name=os.path.join(hsdef.MOVIE_DIR,R_id,hsdef.SRC,filename[:-4]) #mp4 path
        # avi->mp4

        os.popen("ffmpeg -fflags +genpts -i '{input}' -c:v copy -c:a copy '{output}.mp4'".format(input = avi_file_path, output = output_name))

        hs_movie.hsm_requests.update_one({"_id":q["_id"]},{"$set":{"STATUS":hsdef.NO_NEED_CONVERT}})
        seconduri=os.path.join("http://129.254.202.111:30111","requestids",R_id,"statuses",hsdef.NO_NEED_CONVERT)
        requests.put(seconduri)
        
        
        #set filename avi->mp4
        hs_movie.hsm_requests.update_one({"_id":q["_id"]},{"$set":{"FILENAME":filename[:-4]+".mp4"}})
        
    time.sleep(5) 
    
    return True


if __name__ == "__main__":    
    cnt=0
    while True:
        print(cnt)
        AVI2MP4()
        cnt+=1

