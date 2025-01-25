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
