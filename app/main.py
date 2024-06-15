from fastapi import FastAPI, HTTPException
from kubernetes import client, config
from prometheus_client import CollectorRegistry, Gauge, generate_latest
import os

app = FastAPI()

# Load Kubernetes config
config.load_incluster_config()

@app.post("/createDeployment/{deployment_name}")
def create_deployment(deployment_name: str):
    api_instance = client.AppsV1Api()

    container = client.V1Container(
        name=deployment_name,
        image="nginx:latest",
        ports=[client.V1ContainerPort(container_port=80)],
    )
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": deployment_name}),
        spec=client.V1PodSpec(containers=[container]),
    )
    spec = client.V1DeploymentSpec(
        replicas=1,
        template=template,
        selector={'matchLabels': {'app': deployment_name}},
    )
    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=deployment_name),
        spec=spec,
    )

    try:
        api_instance.create_namespaced_deployment(
            namespace="default",
            body=deployment,
        )
        return {"message": f"Deployment {deployment_name} created successfully"}
    except client.ApiException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/getPromdetails")
def get_prom_details():
    registry = CollectorRegistry()
    g = Gauge('running_pods', 'Number of running pods', registry=registry)

    api_instance = client.CoreV1Api()
    pods = api_instance.list_pod_for_all_namespaces(watch=False)

    running_pods = sum(1 for pod in pods.items if pod.status.phase == "Running")
    g.set(running_pods)

    return generate_latest(registry)

