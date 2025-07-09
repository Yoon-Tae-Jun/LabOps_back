from .utils import logger, kubeUtils

class Watcher:
    def __init__(self):
        self.Log = logger.Logger(__file__)
        self.k = kubeUtils.KubeUtils()
    
    def log_generator(self, job_name: str):
        try:
            for line in self.k.stream_job_logs_generator(job_name):
                self.Log.info(f"log: {line}")
                yield line + "\n"
        except Exception as e:
            self.Log.error(f"log: {str(e)}")
            yield f"[ERROR] {str(e)}\n"
