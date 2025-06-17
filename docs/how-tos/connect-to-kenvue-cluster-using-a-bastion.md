# How to connect to kenvue cluster using a bastion

## SSH to bastion

ssh <kenvue account username>@AWSWEXNVAL0001.kenvue.com

## Set up your user enviornment

Install kubectl and aws-iam-authenticator

```
mkdir bin
cd bin
curl -Lo aws-iam-authenticator https://github.com/kubernetes-sigs/aws-iam-authenticator/releases/download/v0.5.9/aws-iam-authenticator_0.5.9_linux_amd64
chmod +x aws-iam-authenticator

cd ..
curl -Lo kuberlr.tar.gz https://github.com/flavio/kuberlr/releases/download/v0.4.2/kuberlr_0.4.2_linux_amd64.tar.gz
tar -xzvf kuberlr.tar.gz

cd kuberlr_0.4.2_linux_amd64/
mv kuberlr ../bin/
cd ../bin
ln -s kuberlr kubectl
cd ..
```

## Configure your ~/.kube/config

```
mkdir .kube
cat << EoF > .kube/config2
apiVersion: v1
clusters:
- cluster:
    server: https://BD0F1A58014FCF446B668A876EE7DF2A.gr7.us-east-1.eks.amazonaws.com
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUM1ekNDQWMrZ0F3SUJBZ0lCQURBTkJna3Foa2lHOXcwQkFRc0ZBREFWTVJNd0VRWURWUVFERXdwcmRXSmwKY201bGRHVnpNQjRYRFRJeU1UQXlOVEV4TlRNMU1Gb1hEVE15TVRBeU1qRXhOVE0xTUZvd0ZURVRNQkVHQTFVRQpBeE1LYTNWaVpYSnVaWFJsY3pDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBT2JpCmFhOUFvSDVlWGpMeFdnQzBONE5JUHVQSVptNmpLNmxBM29sTVAwUHYyd1hlalphcEFsVnFOWVdxcHl3aCtZZm8KT1lLR1Nuc2hPdE9DbnVyU094SVhoY1BnR1ZmN1REVlZGbU04WW5KSzBmOHdLWmxLdDNIYU9oWFJkekNZYkJoMgoydnpZSGx0ZGREbHkvTHpwaWpNQlpNRHY1UUtkeEhNSEF0aUd6aG4xS2xvT2xkRGozV1lpV1VJV0ladzZheWV2CnNhYm1Rd3A1REJwQjBVN3V2bEdMd1RUQ3RZc3NhdnI2dDZ6MWtzNHhNUUMxVTlONUlHV0UxdEUrZGZwMmZzWDYKZ3d1c0tEOGNESkFiVmFrL2lwK3pkcXRxRnJHOVFNeDBEelpQYzRtU1dnVDZyVXZjbTlBbTlrMVNsSXc5ODlGRApHelh6bGxQcXZySWNnU1RWSW9jQ0F3RUFBYU5DTUVBd0RnWURWUjBQQVFIL0JBUURBZ0trTUE4R0ExVWRFd0VCCi93UUZNQU1CQWY4d0hRWURWUjBPQkJZRUZLNnJEeXBRK3VReGgxWU8zS0JKbmthYU1TNUdNQTBHQ1NxR1NJYjMKRFFFQkN3VUFBNElCQVFCdk52clZjRjFaZ1FDMzNpbDZrR0gzcHJJN3RWRmcvOTF3UVNZZkM2SFM2cWRiVERucwpNYXhoeEYvblZzbFEyKzRmN0UxVUZodUdsOUdUZlVvS2FiQzB1cWx6bUpQaDJVUXJRZ3hZQnd3eGxTOSszcHJNCnlUOGZ5M29uM21jaWR0azZlSllIcm5wZS9QZnlWN1J5eUhva0pVVGIwcWFVakxoMVZHVFoyRmJLK0ZjeG50SHcKdWJ4bnlSMHZlcGExdDFoOVljNDFJYnFzUGRBMVFDZVYvR1hNdWN4Z0U4bUd1VFZQQlU1MEdYbG1qWnRZVjg5dgp3TVpYTVVobzNmakdQNVVnMnlFTmtXaW9Ra2hqUkRMRUZGQXpZUzMrSU5TWnAwMklBUTRRNkNSYnJ0Vmc5ZDFrCkY4d1FzaytJUXUrMnE3T25WOUs5cUdYeXdrakNSd0ZTV1N2UwotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: aws
  name: aws
- context:
    cluster: kubernetes
    user: aduser
  name: user
current-context: aws
kind: Config
preferences: {}
users:
- name: aws
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: aws-iam-authenticator
      args:
        - "token"
        - "-i"
        - "itx-wcr-datacove-development"
        - "-r"
        - "arn:aws:iam::551241293703:role/itx/service/EKS/VPCxEKSRole"
- name: aduser
  user:
    auth-provider:
      config:
        apiserver-id: "22f9d484-b818-4b21-a278-00b264446505"
        client-id: "22f9d484-b818-4b21-a278-00b264446505"
        environment: AzurePublicCloud
        tenant-id: "7ba64ac2-8a2b-417e-9b8f-fcf8238f2a56"
      name: azure
EoF
```

## Connect to cluster

```
kubectl get nodes
```
