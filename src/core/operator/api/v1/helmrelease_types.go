package v1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	"helm.sh/helm/v3/pkg/release"
)

// Important: Run "make" to regenerate code after modifying this file

// HelmReleaseSpec defines the desired state of HelmRelease
type HelmReleaseSpec struct {
	// The helm repo url (e.g. https://airflow.apache.org)
	RepoURL string `json:"repoURL"`

	// A name for the helm repo (e.g. apache-airflow)
	RepoName string `json:"repoName"`

	// The chart to install (e.g. apache-airflow/airflow)
	Chart string `json:"chart"`

	// The version of the chart to install (e.g. 1.3.0)
	Version string `json:"version"`

	// The name of a secret containing the values.yaml to configure the chart.
	ValuesName string `json:"valuesName"`
}

// HelmReleaseStatus defines the observed state of HelmRelease
type HelmReleaseStatus struct {
	Status release.Status `json:"status"`
}

//+kubebuilder:object:root=true
//+kubebuilder:subresource:status

// HelmRelease is the Schema for the helmreleases API
type HelmRelease struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   HelmReleaseSpec   `json:"spec,omitempty"`
	Status HelmReleaseStatus `json:"status,omitempty"`
}

//+kubebuilder:object:root=true

// HelmReleaseList contains a list of HelmRelease
type HelmReleaseList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []HelmRelease `json:"items"`
}

func init() {
	SchemeBuilder.Register(&HelmRelease{}, &HelmReleaseList{})
}
