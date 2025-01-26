# Stable Diffusion 3 Hosting on AWS with Istio, KServe, and EKS

This project involves the deployment of a text-to-image generation backend powered by Stable Diffusion 3. It leverages modern cloud-native tools and architectures, including Amazon Elastic Kubernetes Service (EKS), Istio, and KServe, along with monitoring and observability tools like Kiali, Prometheus, and Grafana. The project uses TorchScript to integrate the model, with model weights stored in Amazon S3 and fetched during the bootstrap process.

---

## Key Components and Their Roles

**1. Amazon EKS (Elastic Kubernetes Service)**

- **Role**: Provides a managed Kubernetes environment to host and orchestrate containerized applications, ensuring scalability, reliability, and ease of management.

- **Why Used**: EKS simplifies Kubernetes cluster management and integrates seamlessly with AWS services like S3, IAM, and CloudWatch, making it ideal for hosting cloud-native workloads.

**2. eksctl**

- **Role**: CLI tool for creating and managing EKS clusters.

- **Why Used**: Simplifies the process of creating and configuring EKS clusters, reducing setup complexity.

**3. Istio**

- **Role**: Service mesh that provides traffic management, security, and observability for microservices.

- **Why Used**: Istio is used to ensure secure, controlled communication between services and to enhance traffic observability and resilience in the system.

**4. KServe**

- **Role**: Model serving platform for deploying and managing machine learning models on Kubernetes.

- **Why Used**: KServe provides high-performance, scalable, and easy-to-use inference-serving capabilities with native Kubernetes support. It simplifies serving the Stable Diffusion 3 model and integrates well with Istio.

5. TorchScript

- **Role**: Converts PyTorch models into a format suitable for deployment.

- **Why Used**: Facilitates model deployment by making the model portable and efficient for serving.

**6. Amazon S3**

- **Role**: Object storage service used to store the model weights.

- **Why Used**: Reliable and scalable storage solution that integrates seamlessly with AWS, enabling efficient access to large files during bootstrap.

**7. Monitoring and Observability Tools**

**Kiali**

- **Role**: Visualizes the service mesh topology and provides insights into Istio's components.

- **Why Used**: Helps in understanding and managing service-to-service communication.

**Prometheus**

- **Role**: Monitoring and alerting toolkit for collecting and querying metrics.

- **Why Used**: Provides detailed performance metrics of the system.

**Grafana**

- **Role**: Visualizes data through dashboards and graphs.

- **Why Used**: Creates intuitive dashboards to analyze metrics collected by Prometheus.

<img width="472" alt="image" src="https://github.com/user-attachments/assets/f1cff934-794e-405d-86a2-27664c4dc752" />

---

## Integrate SD3 with Torchscript

**Step - 1**

First we need to download the required model from hugginface: [download_model.py](sd3-kserve/download_model.py)

```python
python download_model.py
```
This will download model weights and store in `sd3-model` directory

**Step - 2**
Now we need to create `.mar` file using model weights. Before we do that we need to create a handler file - [sd3_handler](sd3-kserve/sd3_handler.py)

```bash
The handler does the following:
1. Initialise - Pull model weights from S3 and load model
2. Pre-process input to be accpetable for inference
3. Model inference
4. Post-process output before returning output
```
**Step - 3**
Now that we have the handler ready, we can go ahead and create `.mar` file - [create_mar.sh](sd3-kserve/bash_scripts/create_mar.sh)

```bash
#!/bin/bash

torch-model-archiver \
    --model-name sd3 \
    --version 1.0 \
    --handler sd3_handler.py \
    --requirements-file requirements.txt \
    -f \
    --export-path ./model-store

echo "MAR file created at ../model-store/sd3.mar" 
```
Here we specify handler, directory of model weights and requirements.txt. The output will be mar file stored in `model-store` directory

**Step - 4**
Once the mar file is ready we can proceed to upload to AWS S3 bucket - [upload_to_s3.sh](sd3-kserve/bash_scripts/upload_to_s3.sh)
config file used - [config.properties](sd3-kserve/config/config.properties)

Now the steps to build torchscript model are completed. We move to deployment and inference

---

## Deployment and Inference of Torchscript model

**Step - 1**
We will create a yaml file to deploy our model - [sd3-isvc.yaml](sd3-kserve/deployment/sd3-isvc.yaml)

```yaml
apiVersion: "serving.kserve.io/v1beta1"
kind: "InferenceService"
metadata:
  name: "torchserve-sd3"
spec:
  predictor:
    serviceAccountName: s3-read-only
    pytorch:
      protocolVersion: v1
      storageUri: "s3://sd3-kserve/sd3/"
      image: pytorch/torchserve-kfs:0.12.0-gpu
      resources:
        limits:
          cpu: "8"
          memory: 16Gi
          nvidia.com/gpu: "1"
      env:
        - name: TS_DISABLE_TOKEN_AUTHORIZATION
          value: "true"
```
Run command `kubectl apply -f sd3-isvc.yaml` to create deployment

**Step - 2**
We can track our deployment using below command - 

```bash
# Check pods status
kubectl get pods
kubectl describe pod <pod-name>
```
```bash
# Check deployment status
kubectl get deployment
kubectl describe deployment <deployment-name>
```
```bash
# Check pod logs
kubectl logs -f <pod-name>
```
Above commands will help us understand if our model is ready for inference or not

**Step - 3**
In order to perform inference we will need to fetch below details -

```bash
# fetch host
kubectl get isvc

# output - torchserve-sd3-default.example.com
```

```bash
# fetch endpoint
kubectl get isvc -n istio-system

# output - k8s-istioing-istioing-163c0111d9-c1e5608c48727220.elb.ap-south-1.amazonaws.com
```

**Step - 4**
Now using details from step 3 we perform inference - [test_inference.py](sd3-kserve/test_inference.py)
```python
python test_inference.py
```

---

## Output

**logs of kubernetes resources** - [all_deployments.yaml](sd3-kserve/all_deployments.yaml)

**Pods log**
<img width="1440" alt="Screenshot 2025-01-25 at 3 56 30 PM" src="https://github.com/user-attachments/assets/4d65540e-0a3c-4010-b510-9043eb8603f4" />

**Test Inference**
<img width="1258" alt="Screenshot 2025-01-25 at 4 35 23 PM" src="https://github.com/user-attachments/assets/4d25a6c3-d77f-40aa-92cf-0e9425d563ff" />

**Runtime inference logs**
<img width="1440" alt="Screenshot 2025-01-25 at 4 40 12 PM" src="https://github.com/user-attachments/assets/24824c2f-a373-43b0-a2ab-6c152cd30380" />

---

## Monitoring

### Kiali graph

**Graph Notation**
<img width="1078" alt="Screenshot 2025-01-25 at 4 37 33 PM" src="https://github.com/user-attachments/assets/27a75ee1-3bcc-4802-8560-63c2db7cb6d2" />

**Inference logs on Kiali**
<img width="1074" alt="Screenshot 2025-01-25 at 4 37 57 PM" src="https://github.com/user-attachments/assets/f775fd63-64bc-4b0e-9b7a-c982e3e5f314" />

---

### Grafana

<img width="727" alt="image" src="https://github.com/user-attachments/assets/8429b9f8-cf2d-40b1-b256-2d306979d509" />

---

## SD3 Output

Inference 1
<img width="300" alt="image" src="sd3-kserve/output_images/output_1.jpg" />

Inference 2
<img width="300" alt="image" src="sd3-kserve/output_images/output_2.jpg" />

Inference 3
<img width="300" alt="image" src="sd3-kserve/output_images/output_3.jpg" />

Inference 4
<img width="300" alt="image" src="sd3-kserve/output_images/output_4.jpg" />

Inference 5
<img width="300" alt="image" src="sd3-kserve/output_images/output_5.jpg" />

---


