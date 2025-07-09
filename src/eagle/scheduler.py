import threading, time
from .utils import logger
from .utils import kubeUtils
from dataclasses import dataclass

@dataclass
class Job:
    job_name: str
    image_name: str
    code_file: str
    priority: int


class JobScheduler:
    def __init__(self):
        self.kubeUtil = kubeUtils.KubeUtils()
        self.Log = logger.Logger(__file__)

        self.job_queue = []
        self.job_count = 0

        self.job_status_map = {}
        self.node_user_map = {
            "raspberrypi" : "user",
            "workstation": "inslab-new-ws"
        }

        t1 = threading.Thread(target=self.job_scheduler_loop, daemon=True)
        t1.start()
        
    def job_scheduler_loop(self):
        while True:
            if self.job_queue:
                idle_node = self.kubeUtil.selectIdleNode()
                if idle_node:
                    node_name = idle_node[0]
                    job = self.job_queue.pop(0)
                    user_name = self.node_user_map.get(node_name)

                    self.job_status_map[job.job_name] = 'running'

                    success = self.kubeUtil.applyJob(
                                                job_name = job.job_name, 
                                                code_file = job.code_file, 
                                                image_name = job.image_name,
                                                user_name = user_name, 
                                                node_name = node_name
                                            )

                    if not success:
                        self.job_status_map[job.job_name] = "error"     

                    self.Log.info(f"{job.job_name} is scheduled at {node_name}, status: {self.job_status_map[job.job_name]}")
            
            for job_name, status in list(self.job_status_map.items()):
                if status == "running":
                    try:
                        pod_status = self.kubeUtil.get_job_status(job_name)
                        current_status = pod_status.get("status", "Unknown")

                        # 상태 변화가 있으면 업데이트
                        if current_status != "Running":
                            self.job_status_map[job_name] = current_status
                            self.Log.info(f"{job_name} 상태 갱신됨: {current_status}")

                    except Exception as e:
                        self.Log.error(f"Job 상태 확인 실패 ({job_name}): {str(e)}")

            time.sleep(5)  # 5초마다 체크

    def get_job_status(self, job_name: str):
        print(self.job_status_map)
        return self.job_status_map.get(job_name, False)

    def enqueue_job(self, job_name: str, image_name: str, code_file: str, priority: int):
        job = Job(job_name, image_name, code_file, priority)

        # 우선순위 높음
        if job.priority == 0:  
            self.job_queue.insert(0, job)
            self.job_count += 1
            self.Log.info(f"{job.job_name} is enqueued with high priority at 0")

        # 우선순위 중간
        elif job.priority == 1:  
            insert_index = self.job_count
            for i in reversed(range(self.job_count)):
                if self.job_queue[i].priority == 2:  
                    insert_index = i
            self.job_queue.insert(insert_index, job)
            self.job_count += 1
            self.Log.info(f"{job.job_name} is enqueued with general priority at {insert_index}")

        # 우선순위 낮음
        elif job.priority == 2:
            self.job_queue.append(job)
            self.job_count += 1
            self.Log.info(f"{job.job_name} is enqueued with low priority at {self.job_count - 1}")

        else:
            self.Log.error("Invalid priority given.")
            return None

        self.job_status_map[job_name] = 'enqueue'
        return job_name

