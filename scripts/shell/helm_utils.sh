# Because helm sucks.

helm_releases() {
  [[ $# -ne 1 ]] && {
    echo 'usage: helm_releases <namespace>'
    return 1
  }
  kubectl -n "$1" get secret -l owner=helm -o name | cut -d. -f5 | sort -u
}

helm_release_json() {
  [[ $# -ne 2 ]] && {
    echo 'usage: helm_release_json <namespace> <release>'
    return 1
  }
  namespace="$1"; release="$2"
  kubectl -n "$namespace" get secret "sh.helm.release.v1.$release.v1" \
    -o jsonpath='{.data.release}' | base64 -D | base64 -D | gunzip
}

helm_chart_name() {
  helm_release_json "$@" | jq -r '.chart.metadata.name'
}

helm_chart_json() {
  helm_release_json "$@" | jq '.chart'
}

helm_chart_metadata() {
  helm_chart_json "$@" | jq '.metadata'
}

helm_chart_name_with_repo() {
  [[ $# -ne 2 ]] && {
    echo 'usage: helm_chart_name_with_repo <namespace> <release>'
    return 1
  }
  namespace="$1"; release="$2"
  chart_name=$(helm_chart_name "$namespace" "$release");
  chart=$(helm search repo -r "\v[^/]+/$chart_name\v" -o json | jq -r .[].name)
  echo "$release: $chart"
}

helm_charts() {
  [[ $# -ne 1 ]] && {
    echo 'usage: helm_charts <namespace>'
    return 1
  }
  for rel in $(helm_releases "$1"); do
    helm_chart_name_with_repo "$1" "$rel"
  done
}
