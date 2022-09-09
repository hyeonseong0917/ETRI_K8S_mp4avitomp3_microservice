
from flask import Flask, render_template, request,jsonify
from werkzeug.utils import secure_filename
import os
import os.path
import shutil
import json
from pymongo import MongoClient
import pymongo
import datetime
import sys
sys.path.append('../hslib')
sys.path.append('../hsdef')
import hsdef as hsdef
import hslib as hslib
from playsound import playsound
from flask import send_file
from bson.objectid import ObjectId

#27017
app = Flask(__name__)
client = MongoClient(hsdef.MONGODB_URI,hsdef.MONGODB_PORT)
hs_movie=client[hsdef.CURRENT_DB]
hsm_requests=hs_movie[hsdef.CURRENT_COLLECTION]

# @app.route('/',methods=['GET','POST','PUT'])
# def hello():
#     response_data = {}
#     response_data['Result'] ="hello" 
#     response = app.response_class(response=json.dumps(response_data), status=200, mimetype='application/json')
#     return response

@app.route('/upload')
def render_file():
    return render_template(hsdef.UPLOAD_WEB_FORM)

@app.route('/fileUpload',methods=['GET','POST'])
def upload_file():
    if request.method=='POST': ##file이 input으로 들어오면
        
        f=request.files['file']
        if not os.path.exists(hsdef.TMP): #/tmp
            os.mkdir(hsdef.TMP)

        f.save(secure_filename(f.filename)) # file 저장
        saved_file_path=os.path.abspath(f.filename) 
        copy_file_path=os.path.join(hsdef.TMP,secure_filename(f.filename))
        shutil.copyfile(saved_file_path,copy_file_path) #/tmp/디렉토리에 mp4저장
        print("FILENAME: ",secure_filename(f.filename))
        # db
        req={
            "DIR":hsdef.SRC,
            "FILENAME":f.filename,
            "STATUS": hsdef.ENQUEUE,
            "STARTTIME": datetime.datetime.now(),
            "AVITOMP4_START_TIME": "NOT STARTED",
            "AVITOMP4_END_TIME": "NOT STARTED",
            "MP4TOMP3_START_TIME": "NOT STARTED",
            "MP4TOMP3_END_TIME": "NOT STARTED",
            "PERIOD": "NOT STARTED",
            "CURPOD": hsdef.POD1,
        }
        # availableFlag=secure_filename(f.filename)[-3:] # mp4인지 avi인지 확인
        # if availableFlag=="mp4":
        #     req["Avail"]=hsdef.AVAIL
        #     req["AVITOMP4_START_TIME"]="NOT AVI"
        #     req["AVITOMP4_END_TIME"]="NOT AVI"
        # else:
        #     req["Avail"]=hsdef.UNAVAIL

        R_id=hs_movie.hsm_requests.insert_one(req).inserted_id # req dict를 collection에 insert
        
        MountReqDir=os.path.join(hsdef.MNT,"movies",str(R_id))
        os.mkdir(MountReqDir) #Request_ID 디렉토리 생성
        RequestSrcDir=os.path.join(MountReqDir,hsdef.SRC)
        os.mkdir(RequestSrcDir) #/R_ID/Source 디렉토리 생성
        
        fileSrc=os.path.join(hsdef.TMP,secure_filename(f.filename))
        fileTar=os.path.join(hsdef.MNT,"movies",str(R_id),hsdef.SRC,secure_filename(f.filename))
        shutil.copyfile(fileSrc,fileTar) # /tmp/에 있는 mp4 혹은 avi를 /mnt/movies/R_ID/Source/로 복사
        
        firstResPath=os.path.join(hsdef.MNT,hsdef.RESULT_OR_BACK_WEB_FORM)
        firstResDir=os.path.join(hsdef.WORKDIR,"templates",hsdef.RESULT_OR_BACK_WEB_FORM)
        shutil.copyfile(firstResPath,firstResDir) # /mnt/resultorback.html을 /templates/resultorback.html로 복사
        
        return render_template(hsdef.RESULT_OR_BACK_WEB_FORM,ID=str(R_id))

@app.route('/result',methods=['GET','POST'])
def result():
    result_DB=[]
    for d in hs_movie[hsdef.CURRENT_COLLECTION].find():
        result_DB.append(d)        
    return render_template(hsdef.RESULT,result_DB=result_DB)    

@app.route('/<R_id>/download',methods=['GET','POST'])        
def Download(R_id):
    hs_doc=hsm_requests.find({})
    for to_delete in hs_doc:
        if str(to_delete["_id"])==R_id:
            hs_movie.hsm_requests.update_one({"_id":to_delete["_id"]},{"$set":{"STATUS":hsdef.DELETED}})
            break           
    return send_file(os.path.join("/mnt/movies",str(R_id),hsdef.TG,str(R_id)+".mp3"),as_attachment=True)

@app.route('/<R_id>/delete',methods=['GET','POST'])    
def Delete(R_id):
    hs_doc=hsm_requests.find({})
    for to_delete in hs_doc:
        if str(to_delete["_id"])==R_id:
            hs_movie.hsm_requests.delete_one({"_id":to_delete["_id"]})
            shutil.rmtree(os.path.join("/mnt","movies",str(R_id)))
            break
    return render_template("resdelete.html",ID=str(R_id))

@app.route('/requestids/<request_id>/statuses/<status>',methods=['PUT','GET','POST'])    
def update_request_status(request_id,status):
    print('request_id=',request_id,status)
    
    hs_query={"_id":ObjectId(request_id)}
    hs_doc=hsm_requests.find(hs_query)
    if status == hsdef.CREATING_MP3:
        hs_movie.hsm_requests.update_one({"_id":ObjectId(request_id)},{"$set":{"MP4TOMP3_START_TIME":datetime.datetime.now()}})
        curPod=""
        for i in hs_doc:
            curPod=(i["CURPOD"]+"->MP4toMP3POD")
        hs_movie.hsm_requests.update_one({"_id":ObjectId(request_id)},{"$set":{"CURPOD":curPod}})                     
    elif status== hsdef.COMPLETE_MP3:
        curPod=""
        for i in hs_doc:
            curPod=(i["CURPOD"]+"->MP4toMP3POD")
        hs_movie.hsm_requests.update_one({"_id":ObjectId(request_id)},{"$set":{"CURPOD":curPod}})            
        hs_movie.hsm_requests.update_one({"_id":ObjectId(request_id)},{"$set":{"MP4TOMP3_END_TIME":datetime.datetime.now()}})
        curTime=datetime.datetime.now()
        for i in hs_doc:
            curTime=i["STARTTIME"]
        hs_movie.hsm_requests.update_one({"_id":ObjectId(request_id)},{"$set":{"PERIOD":str(datetime.datetime.now()-curTime)}})    
    elif status == hsdef.NEED_CONVERT:
        curPod=""
        for i in hs_doc:
            curPod=(i["CURPOD"]+"->AVItoMP4POD")
        hs_movie.hsm_requests.update_one({"_id":ObjectId(request_id)},{"$set":{"CURPOD":curPod}})            
        hs_movie.hsm_requests.update_one({"_id":ObjectId(request_id)},{"$set":{"AVITOMP4_START_TIME":datetime.datetime.now()}}) 
    elif status==hsdef.NO_NEED_CONVERT:
        curPod=""
        for i in hs_doc:
            curPod=(i["CURPOD"]+"->AVItoMP4POD")
        hs_movie.hsm_requests.update_one({"_id":ObjectId(request_id)},{"$set":{"CURPOD":curPod}})            
        hs_movie.hsm_requests.update_one({"_id":ObjectId(request_id)},{"$set":{"AVITOMP4_END_TIME":datetime.datetime.now()}})
    return jsonify({"status":status})
       

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True,threaded=True)        
