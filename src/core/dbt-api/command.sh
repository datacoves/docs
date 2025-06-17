#!/bin/sh
# Exit the script immediately if any command returns a non-zero exit status.
set -e

if [ "$1" == "forward_postgres" ]; then

  kubectl port-forward --namespace core svc/postgres-postgresql 5432:5432

elif [ "$1" == "forward_airflow" ]; then

  kubectl port-forward --namespace dcw-dev123 svc/dev123-airflow-postgresql 5433:5432

elif [ "$1" == "forward_minio" ]; then

  kubectl port-forward -n core svc/minio 9000 9001

elif [ "$1" == "delete_airflow" ]; then

  services=$(kubectl get services --all-namespaces -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' | grep -E '(airflow|minio)')
  deployments=$(kubectl get deployments --all-namespaces -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' | grep -E '(airflow|minio)')

  for service in $services; do
    kubectl delete service $service --namespace dcw-dev123
  done

  for deployment in $deployments; do
    kubectl delete deployment $deployment --namespace dcw-dev123
  done

else

  echo "Command $1 unknown!"

fi
