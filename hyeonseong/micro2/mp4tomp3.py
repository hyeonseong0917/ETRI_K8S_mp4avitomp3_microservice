from crypt import methods
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import requests
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
import requests
from bson.objectid import ObjectId
import time

client = MongoClient(hsdef.MONGODB_URI,hsdef.MONGODB_PORT)
hs_movie=client[hsdef.CURRENT_DB]
hsm_requests=hs_movie[hsdef.CURRENT_COLLECTION]

#MP4 TO MP3
def mp4tomp3():
    # find mp4(Available)
    hs_query={"STATUS":hsdef.NO_NEED_CONVERT}
    hs_doc=hsm_requests.find(hs_query)
    # print("111")
    # r=request.put("http://129.254.202.111:30111/")
    # print("222")
    for toConvert in hs_doc:
        R_id=str(toConvert["_id"]) # get ObjectId
        hs_movie.hsm_requests.update_one({"_id":toConvert["_id"]},{"$set":{"STATUS":hsdef.CREATING_MP3}})
        
        #To Record Time In Pod1, Use API
        firsturi=os.path.join("http://129.254.202.111:30111","requestids",R_id,"statuses",hsdef.CREATING_MP3)
        requests.put(firsturi)
        
        
        #mp4 path
        mp4_name=toConvert["FILENAME"]
        mp4_file_path = os.path.join(hsdef.MOVIE_DIR,R_id,hsdef.SRC,mp4_name) # /mnt/movies/<R_id>/Source/

        #mp3 path
        mp3_name=R_id+".mp3"
        mp3_file_path=os.path.join(hsdef.MOVIE_DIR,R_id,hsdef.TG,mp3_name)
        if not os.path.exists(os.path.join(hsdef.MOVIE_DIR,R_id,hsdef.TG)):
            os.mkdir(os.path.join(hsdef.MOVIE_DIR,R_id,hsdef.TG))

        #mp4tomp3
        videoclip = VideoFileClip(mp4_file_path)
        if not os.path.exists(mp3_file_path):
            audioclip = videoclip.audio
            audioclip.write_audiofile(mp3_file_path)
            audioclip.close()
        videoclip.close()
        hs_movie.hsm_requests.update_one({"_id":toConvert["_id"]},{"$set":{"STATUS":hsdef.COMPLETE_MP3}})
        seconduri=os.path.join("http://129.254.202.111:30111","requestids",R_id,"statuses",hsdef.COMPLETE_MP3)
        requests.put(seconduri)
        
        #DB status Update
        if not os.path.exists(mp3_file_path):
            hs_movie.hsm_requests.update_one({"_id":toConvert["_id"]},{"$set":{"STATUS":"mp4 to mp3 err"}})    
        else:
            hs_movie.hsm_requests.update_one({"_id":toConvert["_id"]},{"$set":{"DIR":mp3_file_path}})

    time.sleep(5)
cnt=0
while True:
    
    mp4tomp3()
    print(cnt)
    cnt+=1
# if __name__ == "__main__":
    
        
