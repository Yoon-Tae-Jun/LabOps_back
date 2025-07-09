from kubernetes import client, config, watch
import time

class KubeUtils:
    def __init__(self):
        config.load_kube_config() # local에서 실행 시
        #config.load_incluster_config() # container에서 실행 시
        self.CoreApi = client.CoreV1Api()
        self.AppApi = client.AppsV1Api()
        self.batchApi = client.BatchV1Api()
        self.rbac_api = client.RbacAuthorizationV1Api()
    
    def create_cluster_role_and_binding(self):
        cluster_role_name = "read-nodes-and-pods-role"
        cluster_role_binding_name = "read-nodes-and-pods-binding"
        service_account_name = "default"
        namespace = "default"

        try:
            cluster_role = client.V1ClusterRole(
                metadata=client.V1ObjectMeta(name=cluster_role_name),
                rules=[
                    client.V1PolicyRule(
                        api_groups=[""],
                        resources=["nodes", "pods"],
                        verbs=["list"]
                    )
                ]
            )

            cluster_role_binding = client.V1ClusterRoleBinding(
                metadata=client.V1ObjectMeta(name=cluster_role_binding_name),
                subjects=[
                    client.RbacV1Subject(
                        kind="ServiceAccount",
                        name=service_account_name,
                        namespace=namespace
                    )
                ],
                role_ref=client.V1RoleRef(
                    kind="ClusterRole",
                    name=cluster_role_name,
                    api_group="rbac.authorization.k8s.io"
                )
            )

            rbac_api = client.RbacAuthorizationV1Api()
            
            # ClusterRole 생성
            try:
                rbac_api.create_cluster_role(body=cluster_role)
                print("[OK] ClusterRole created.")
            except client.exceptions.ApiException as e:
                if e.status == 409:
                    print("[INFO] ClusterRole already exists.")
                else:
                    print("[ERROR] Failed to create ClusterRole:", e)

            # ClusterRoleBinding 생성
            try:
                rbac_api.create_cluster_role_binding(body=cluster_role_binding)
                print("[OK] ClusterRoleBinding created.")
            except client.exceptions.ApiException as e:
                if e.status == 409:
                    print("[INFO] ClusterRoleBinding already exists.")
                else:
                    print("[ERROR] Failed to create ClusterRoleBinding:", e)

        except Exception as e:
            print("[FATAL] Unexpected error during role setup:", e)

    def create_role_and_binding(self, namespace="default"):
        role_name = "pod-access-role"
        role_binding_name = "pod-access-rolebinding"
        service_account_name = "default"

        # Role 정의
        role = client.V1Role(
            metadata=client.V1ObjectMeta(name=role_name, namespace=namespace),
            rules=[
                client.V1PolicyRule(
                    api_groups=[""],
                    resources=["pods", "pods/log"],
                    verbs=["get", "list", "watch"]
                ),
                # Job 생성 및 읽기 권한
                client.V1PolicyRule(
                    api_groups=["batch"],
                    resources=["jobs"],
                    verbs=["create"]
                )
            ]
        )

        # RoleBinding 정의
        role_binding = client.V1RoleBinding(
            metadata=client.V1ObjectMeta(name=role_binding_name, namespace=namespace),
            subjects=[
                {
                    "kind":"ServiceAccount",
                    "name":service_account_name,
                    "namespace":namespace
                }
            ],
            role_ref=client.V1RoleRef(
                kind="Role",
                name=role_name,
                api_group="rbac.authorization.k8s.io"
            )
        )

        # Role 생성
        try:
            self.rbac_api.create_namespaced_role(namespace=namespace, body=role)
            print(f"Role '{role_name}' created")
        except ApiException as e:
            if e.status == 409:
                print(f"Role '{role_name}' already exists")
            else:
                raise
        # RoleBinding 생성
        try:
            self.rbac_api.create_namespaced_role_binding(namespace=namespace, body=role_binding)
            print(f"RoleBinding '{role_binding_name}' created")
        except ApiException as e:
            if e.status == 409:
                print(f"RoleBinding '{role_binding_name}' already exists")
            else:
                raise

    ## 오브젝트 조회 ##
    def selectPod(self):
        print("=========[SELECT Pod]=========")
        pods = self.CoreApi.list_pod_for_all_namespaces(watch=False)
        for pod in pods.items:
            print(f"{pod.metadata.namespace}\t{pod.metadata.name}\t{pod.status.phase}")

    def selectDeployment(self):

        print("=========[SELECT Deployments]=========")
        deployments = self.AppApi.list_namespaced_deployment(namespace="default")
        for deploy in deployments.items:
            print(f"- name: {deploy.metadata.name}")
            print(f"  replica: {deploy.status.ready_replicas}/{deploy.status.replicas}")
            print(f"  label: {deploy.metadata.labels}")
            print()

    def selectService(self):

        print("=========[SELECT Services]=========")
        services = self.CoreApi.list_namespaced_service(namespace="default")
        for svc in services.items:
            print(f"  name: {svc.metadata.name}")
            print(f"  type: {svc.spec.type}")
            print(f"  port mapping:")
            for port in svc.spec.ports:
                print(f"    {port.port} → {port.target_port}")
            print(f"  selector: {svc.spec.selector}")
            print()

    def selectIdleNode(self, label_selector="role=workstation"):
        active_node = []
        self.CoreApi = client.CoreV1Api()
        nodes = self.CoreApi.list_node(label_selector=label_selector).items
        for node in nodes:
            node_name = node.metadata.name
            pods = self.CoreApi.list_pod_for_all_namespaces(
                field_selector=f"spec.nodeName={node_name}"
            ).items

            active_jobs = [
                p for p in pods
                if p.metadata.labels.get("type") == "training"
            ]
            if not active_jobs:
                active_node.append(node_name)  # 이 노드는 비어있음!

        return active_node

    ## 오브젝트 삭제 ##
    def deleteDeployment(self, target, namespace):
        print("=========[Delete Deployment]=========")
        deployments = self.AppApi.list_namespaced_deployment(namespace=namespace)
        for deploy in deployments.items:
            name = deploy.metadata.name
            if name.startswith(target):
                print(f"- deleting: {name}")
                self.AppApi.delete_namespaced_deployment(
                    name=name,
                    namespace=namespace,
                    body=client.V1DeleteOptions()
                )

    def deleteService(self, target, namespace):
        print("=========[Delete Service]=========")
        services = self.CoreApi.list_namespaced_service(namespace=namespace)
        for svc in services.items:
            name = svc.metadata.name
            if name.startswith(target):
                print(f"- deleting: {name}")
                self.CoreApi.delete_namespaced_service(
                    name=name,
                    namespace=namespace
                )


    ## 오브젝트 추가 ##
    def applyDeployment(self, deploymentName, podName, nodeName, imageName, memory, cpu, port, policy):

        deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(name=deploymentName),
        spec=client.V1DeploymentSpec(
            replicas=2,
            selector={"matchLabels": {"app": podName}},
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": podName}),
                spec=client.V1PodSpec(
                    node_name= nodeName,  # ← master node만 사용하도록 지정
                    containers=[
                        client.V1Container(
                            name= podName,
                            image= imageName,
                            image_pull_policy= policy,
                            resources=client.V1ResourceRequirements(
                                limits={"memory": memory, "cpu": cpu}
                            ),
                            ports=[client.V1ContainerPort(container_port=port)]
                        )
                    ]
                )
            )
        ))
        self.AppApi.create_namespaced_deployment(namespace="default", body=deployment)
        print("success apply deployment\n")

    def applyService(self, serviceName, TargetName, exposePort, TargetPort, serviceType):

        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=serviceName),
            spec=client.V1ServiceSpec(
                selector={"app": TargetName},
                ports=[client.V1ServicePort(port= exposePort, target_port= TargetPort)],
                type= serviceType
        ))

        self.CoreApi.create_namespaced_service(namespace="default", body=service)
        print("success apply Service\n")

    def applyJob(self, job_name: str, code_file: str, image_name:str, user_name:str, node_name: str):

        #IMAGE_NAME = "python:3.10"
        #IMAGE_NAME = "nvcr.io/nvidia/tensorflow:23.11-tf2-py3"
        HOST_PATH = f"/home/{user_name}/k3s/nfs-share/project/p2/code"  # 실제 서버 경로
        MOUNT_PATH = "/mnt/code"                           # Pod 내부에서 바라보는 경로
        NODE_NAME = node_name

        container = client.V1Container(
            name="training",
            image=image_name,
            command=["python", f"{MOUNT_PATH}/{code_file}"],  # /mnt/code/t1.py
            volume_mounts = [client.V1VolumeMount(
                name="code-volume",
                mount_path=MOUNT_PATH
            )],
            resources=client.V1ResourceRequirements(
                limits={"nvidia.com/gpu": "1"}
            ),
            env=[
                client.V1EnvVar(name="CUDA_VISIBLE_DEVICES", value="1")
            ]
        )

        volume = client.V1Volume(
            name="code-volume",
            host_path=client.V1HostPathVolumeSource(
                path=HOST_PATH
            )
        )

        job = client.V1Job(
            metadata=client.V1ObjectMeta(
                name=job_name
            ),
            spec=client.V1JobSpec(
                ttl_seconds_after_finished=5,
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"job": job_name, "type": "training"}),
                    spec=client.V1PodSpec(
                        containers=[container],
                        restart_policy="Never",
                        node_name=NODE_NAME,
                        volumes=[volume],
                    )
                )
            )
        )
        try:
            self.batchApi.create_namespaced_job(namespace="default", body=job)
            return True
        except ApiException as e:
            return False    

    def get_job_status(self, job_name: str):
        NAMESPACE = "default"
        pods = self.CoreApi.list_namespaced_pod(
            namespace=NAMESPACE,
            label_selector=f"job={job_name}"
        )

        if not pods.items:
            return "NotFound"
        
        latest_pod = sorted(
            pods.items,
            key=lambda p: p.metadata.creation_timestamp,
            reverse=True
        )[0]

        return {
            "pod_name": latest_pod.metadata.name,
            "status": latest_pod.status.phase or "Unknown",
            "node_name": latest_pod.spec.node_name
        }

    def stream_job_logs_generator(self, job_name: str):
        NAMESPACE = "default"
        log_lines = []

        while True:
            pod_status = self.get_job_status(job_name)

            if pod_status["status"] == "NotFound":
                yield f"[오류] Job={job_name} 에 해당하는 Pod이 없습니다."
                time.sleep(5)
                continue
            elif pod_status["status"] != "Running":
                yield f"[대기 중] Job={job_name} 의 상태가 {pod_status['status']} 입니다."
                time.sleep(5)
                continue
            elif pod_status["status"] == "Running":
                yield f"[실행중] Pod: {pod_name}, Node: {node_name}"

                w = watch.Watch()
                try:
                    for line in w.stream(
                        self.CoreApi.read_namespaced_pod_log,
                        name=pod_name,
                        namespace=NAMESPACE,
                        follow=True,
                        _preload_content=False
                    ):
                        decoded = line.decode("utf-8")
                        yield line
                        log_lines.append(decoded)
                except Exception as e:
                    yield f"[에러] 로그 스트림 실패: {str(e)}"
                break
        save_path = f"./{job_name}.log"
        with open(job_name, "w", encoding="utf-8") as f:
            f.writelines(log_lines)
        yield f"[save]log file saved at {save_path}"

