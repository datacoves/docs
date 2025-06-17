# Self hosted Github Runner
1. Create new runnner [in Github](https://github.com/datacoves/datacoves/settings/actions/runners). You must have `Owner` privileges.
3. Create a virtual machine, e.g. in Azure, and run the scritps that Github gave you on the previous step.
3. Install dependencies on the machine you created

```bash
# Update and Upgrade
sudo apt-get update
sudo apt-get upgrade -y

# Add Kubernetes repository and key
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee -a /etc/apt/sources.list.d/kubernetes.list

# Add Helm repository and key
curl https://baltocdn.com/helm/signing.asc | sudo apt-key add -
echo "deb https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list

# Update package list again after adding the Kubernetes and Helm repositories
sudo apt-get update

# Install software/packages
sudo apt-get install -y apt-transport-https gnupg2 kubectl tmux python3-pip docker.io golang helm

# Python symbolic link
sudo ln -s /usr/bin/python3 /usr/bin/python

# Docker post-installation step for the current user
sudo usermod -aG docker $USER

# Go and kind installation
go install sigs.k8s.io/kind@v0.20.0
sudo ln -s /home/datacoves/go/bin/kind /usr/local/bin/kind
```
4. run `tmux` to do not close the session when detached from ssh connection.
5. Follow any instruction you got from Github on step 1 and install the runner as a service: `sudo ./svc.sh install datacoves`
6. Boost inotify limits for system performance. Update the following values in the specified files:

    ```Boost inotify limits for system performance. Update the following values in the specified files:
    ~$ cat /proc/sys/fs/inotify/max_user_instances
    1024
    ~$ cat /proc/sys/fs/inotify/max_user_watches
    524288
    ~$ cat /proc/sys/fs/inotify/max_queued_events
    16384
    ```