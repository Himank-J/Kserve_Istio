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

aws configure

sudo snap install kubectl --classic

eksctl create cluster -f eks-cluster.yaml

eksctl utils associate-iam-oidc-provider --region ap-south-1 --cluster eks-cluster-kserve --approve

helm repo add istio https://istio-release.storage.googleapis.com/charts

kubectl create namespace istio-system

helm install istio-base istio/base \
  --version 1.20.2 \
  --namespace istio-system --wait

helm install istiod istio/istiod \
  --version 1.20.2 \
  --namespace istio-system --wait

kubectl create namespace istio-ingress

helm install istio-ingress istio/gateway \
  --version 1.20.2 \
  --namespace istio-ingress \
  --set labels.istio=ingressgateway \
  --set service.annotations."service\\.beta\\.kubernetes\\.io/aws-load-balancer-type"=external \
  --set service.annotations."service\\.beta\\.kubernetes\\.io/aws-load-balancer-nlb-target-type"=ip \
  --set service.annotations."service\\.beta\\.kubernetes\\.io/aws-load-balancer-scheme"=internet-facing \
  --set service.annotations."service\\.beta\\.kubernetes\\.io/aws-load-balancer-attributes"="load_balancing.cross_zone.enabled=true" 

helm ls -n istio-system
helm ls -n istio-ingress

kubectl rollout restart deployment istio-ingress -n istio-ingress

kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

for ADDON in kiali jaeger prometheus grafana
do
    ADDON_URL="https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/$ADDON.yaml"
    kubectl apply -f $ADDON_URL
done

kubectl label namespace default istio-injection=enabled

kubectl get crd gateways.gateway.networking.k8s.io &> /dev/null || \
  { kubectl kustomize "github.com/kubernetes-sigs/gateway-api/config/crd?ref=v1.2.0" | kubectl apply -f -; }

eksctl create iamserviceaccount \
--cluster=eks-cluster-kserve \
--namespace=kube-system \
--name=aws-load-balancer-controller \
--attach-policy-arn=arn:aws:iam::390430468701:policy/AWSLoadBalancerControllerIAMPolicy \
--override-existing-serviceaccounts \
--region ap-south-1 \
--approve

helm repo add eks https://aws.github.io/eks-charts

helm install aws-load-balancer-controller eks/aws-load-balancer-controller -n kube-system --set clusterName=eks-cluster-kserve --set serviceAccount.create=false --set serviceAccount.name=aws-load-balancer-controller

kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/bookinfo/platform/kube/bookinfo.yaml

kubectl exec "$(kubectl get pod -l app=ratings -o jsonpath='{.items[0].metadata.name}')" -c ratings -- curl -sS productpage:9080/productpage | grep -o "<title>.*</title>"

kubectl apply -f istio-kserve-ingress.yaml

kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.2/cert-manager.yaml

# install kserve crd
helm install kserve-crd oci://ghcr.io/kserve/charts/kserve-crd --version v0.14.1

helm install kserve oci://ghcr.io/kserve/charts/kserve \
  --version v0.14.1 \
  --set kserve.controller.deploymentMode=RawDeployment \
  --set kserve.controller.gateway.ingressGateway.className=istio

# test kserve
kubectl apply -f test_kserve/iris.yaml

kubectl get inferenceservice

# s3 access for kserve
eksctl create iamserviceaccount \
	--cluster=eks-cluster-kserve \
	--name=s3-read-only \
	--attach-policy-arn=arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess \
	--override-existing-serviceaccounts \
	--region ap-south-1 \
	--approve

kubectl apply -f s3-secret.yaml

kubectl patch serviceaccount s3-read-only -p '{"secrets": [{"name": "s3-secret"}]}'
