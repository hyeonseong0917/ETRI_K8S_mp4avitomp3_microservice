kubectl delete -f ./micro1/hyeonseong-reqDeploy.yaml &&
sudo docker build -t hsr -f ./micro1/docker/Dockerfile . &&
sudo docker tag hsr hyeonseong0917/hsr &&
sudo docker push hyeonseong0917/hsr &&
kubectl apply -f ./micro1/hyeonseong-reqDeploy.yaml