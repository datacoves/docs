# List python processes running on certain namespace's code server pods

```bash
#!/bin/bash
ns="dcw-dev001
pods=$(kubectl -n $ns get pods | grep code-server | awk '{print $1, $8}')
for pod in $pods; do
  kubectl -n $ns exec -ti $pod -- bash -c 'ps auxwf' | grep python
done
```
