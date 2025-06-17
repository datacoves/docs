package v1

import (
	"fmt"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// NOTE: Run "make" to regenerate code after modifying this file.

// AccountSpec defines the desired state of Account
type AccountSpec struct {
	// The docker image registry to pull images from. Empty implies dockerhub.
	ImageRegistry string `json:"imageRegistry"`

	// +optional
	ImagePullSecret string `json:"imagePullSecret,omitempty"`

	// A map of the docker images used. Maps image names to tags (versions).
	Images map[string]string `json:"images"`

	// Map the name of a config to the name of a resource containing its current value.
	Configs map[string]string `json:"configs"`
}

// AccountStatus defines the observed state of Account
type AccountStatus struct {
}

//+kubebuilder:object:root=true
//+kubebuilder:subresource:status

// Account is the Schema for the accounts API
type Account struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   AccountSpec   `json:"spec,omitempty"`
	Status AccountStatus `json:"status,omitempty"`
}

func (a *Account) ImageName(img string) string {
	registry := a.Spec.ImageRegistry
	tag := "latest" // TODO: Might not want to fallback to latest.
	if t, found := a.Spec.Images[img]; found {
		tag = t
	}
	if registry != "" {
		registry += "/"
	}
	return fmt.Sprintf("%s%s:%s", registry, img, tag)
}

//+kubebuilder:object:root=true

// AccountList contains a list of Account
type AccountList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []Account `json:"items"`
}

func init() {
	SchemeBuilder.Register(&Account{}, &AccountList{})
}
