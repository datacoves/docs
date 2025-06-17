#!/bin/bash

# Set the namespace where your pods reside
NAMESPACE="dcw-gay725"

# Get the list of pods with the status "Error"
PODS_ERROR=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Failed -o jsonpath='{.items[*].metadata.name}')

# Check if there are any pods with the status "Error"
if [ -z "$PODS_ERROR" ]; then
  echo "No pods with the status 'Error' found in namespace '$NAMESPACE'. Nothing to delete."
  exit 0
fi

# Loop through the list of pods with the status "Error" and delete them
for POD_NAME in $PODS_ERROR; do
  kubectl delete pod "$POD_NAME" -n "$NAMESPACE"
done

echo "Deleted all pods with the status 'Error' in namespace '$NAMESPACE'."
