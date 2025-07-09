from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .scheduler import JobScheduler
from .watcher import Watcher
from .apiLoader import ApiLoader
from typing import Any

eagle_router = APIRouter()

j = JobScheduler()
w = Watcher()
a = ApiLoader("192.168.10.15","8002")

# 요청 바디 모델
class JobRequest(BaseModel):
    job_name: str
    project_name: str
    image_name: str
    code_file: str
    priority: str
    description: str

class Response(BaseModel):
    status_code: int
    message: str
    data: Any

@eagle_router.get("/image/list", response_model=Response)
def get_images():
    return Response(
        status_code=200,
        message="image list successed!",
        data= ["python:3.10", "nvcr.io/nvidia/tensorflow:23.11-tf2-py3", "tensorflow/tensorflow:2.19.0-gpu"]
    )

@eagle_router.get("/code/list")
def get_code_list():
    return Response(
        status_code=200,
        message="code path list successed!",
        data= ["t2.py", "t3.py", "t4.py", "t5.py"]
    )
    
@eagle_router.post("/train")
def enqueue_job(req: JobRequest):
    job_name = j.enqueue_job(req.job_name, req.image_name, req.code_file, 1)
    return Response(
        status_code=200,
        message="enqueued job successed!",
        data= {"job_name": job_name}
    )

@eagle_router.get("/queue")
def get_queue():
    return Response(
        status_code=200,
        message="get queue successed!",
        data= {"queue": j.job_queue}
    )

@eagle_router.get("/logs/{job_name}")
def stream_logs(job_name: str):
    return StreamingResponse(w.log_generator(job_name), media_type="text/plain")

@eagle_router.get("/job/status/{job_name}")
def get_job_status(job_name: str):
    return Response(
        status_code=200,
        message="get queue successed!",
        data= j.get_job_status(job_name)
    )

@eagle_router.get("/folder/{user_name}")
def get_folder_list(user_name: str):
    return Response(
        status_code=200,
        message="get queue successed!",
        data= a.loadFolderList(user_name)
    )

