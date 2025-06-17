# Configure Bastion EC2 instance

## JNJ

Name: 
Host: AWSAZTIRLL000Q.jnj.com

### SSH to instance

1. In your AWS workspace/Microsoft Remote Desktop (windows) open a terminal `ssh 10.157.82.138 -m hmac-sha2-512` or
2. Create a shortcut to ssh pointing to `C:\Windows\System32\OpenSSH\ssh.exe 10.157.82.138 -m hmac-sha2-512`
3. Click on the shortcut and type your password to access the instance

## CHAP

Name: itx-wcr-EKS workstation
Host: awswcrnval001n.kenvue.com

### Request role

In your **Remote Desktop** go to [IAM](iam.kenvue.com):

1. Request / Star a new request
2. Request the following roles:
   - ITS-ITX-WCR-Datacove-Prd-K8sOperator
   - ITS-ITX-WCR-Datacove-Prd-K8sMonitor
   - ITS-ITX-WCR-Datacove-Prd-K8sAdmin
   - ITS-EP-AWSWCRNVAL001N-LINUX-NA-UNIXSEAdmins
3. Details:
   - Job role: Datacoves Support
   - Application ID: APP000300001207
   - Application Name: DATACOVES-ANALYTICS PRODUCTION WORKBENCH FOR ELT & ORCHESTRATION
   - Describe, in detail, the job functions you perform that REQUIRE this level of privilege: We maintain and support the Datacoves application which runs on Kubernetes.
   - Is the Application Software (includes Web Components, Vendor Application), installed on the Server on which you are requesting Admin Access? No / Yes: No
   - Frequency of Need: Weekly
4. Submit

### SSH to instance

1. On the terminal run command `ssh 10.79.29.123`
2. Your user should be added to the following groups in `/etc/groups`

## Create your working directory

Create your working directory under `/app/users`, i.e. `/app/users/ssassi`.

### Grant you access to docker

```shell
sudo su -
vi /etc/group
```

Example:

```shell
datacoves:x:8653:amorer01,<my-user>  # To chap
docker:x:187:amorer01,<my-user>
```

### Configure your home folder (~)

1. Copy the contents of `/app/users/datacoves-home-template` to your home folder:

```shell
cp -R /app/users/datacoves-home-template/. ~/
```

2. Exit and reconnect to the instance to ensure that the `.bashrc` script was ran accordingly
3. Fix kubelogin permissions

```shell
asdf uninstall kubelogin
asdf install kubelogin
```

5. Configure your credentials to the clusters

```shell
kc config get-contexts
kc config use-context <choose one>
kc get ns
```

Note: you'll need to change your ~/.kube/config permissions:

```shell
chmod 600 ~/.kube/config
```

## Clone datacoves deployment repo

```shell
/app/users/<your username>
git clone https://sourcecode.jnj.com/scm/asx-ahrx/datacoves_deployment.git
```

After clonning, follow the instructions to reveal secrets and install requirements.
