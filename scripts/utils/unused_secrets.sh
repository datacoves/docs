#!/bin/bash

read -p "Namespace? " namespace

depSecrets=$(kubectl -n "$namespace" get deploy -o jsonpath='{.items[*].spec.template.spec.volumes[*].secret.secretName}' | xargs -n1 | grep user-secrets)

# Get the secrets to be deleted
secretsToDelete=$(comm -13 \
    <(echo "$depSecrets" | sort | uniq) \
    <(kubectl -n "$namespace" get secrets -o jsonpath='{.items[*].metadata.name}' | xargs -n1 | grep user-secrets | sort | uniq))

# Display the secrets to be deleted
echo "Secrets to be deleted in namespace $namespace:"
echo "$secretsToDelete"

# Ask for confirmation
read -p "Do you want to delete these secrets? (y/n): " confirm

if [ "$confirm" == "y" ]; then
    # Perform the deletion
    echo "$secretsToDelete" | xargs -I{} kubectl -n "$namespace" delete secret "{}"

    echo "Secrets deleted successfully."
else
    echo "Deletion canceled."
fi
