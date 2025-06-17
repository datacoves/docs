package v1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

/*
 * NOTE: Run "make" to regenerate code after modifying this file.
 *
 * ALSO: remember to edit the 'Equals' function immediately below this
 * structure.
 */

// UserSpec defines the desired state of User
type UserSpec struct {
	// The user's email.
	Email string `json:"email"`

	// The user's name
	Name string `json:"name"`

	// A slug used in urls.
	// +kubebuilder:validation:Pattern=[a-z]([-a-z0-9]*[a-z0-9])?
	Slug string `json:"slug"`

	// The permissions to have access to the workspace services
	Permissions []PermissionSpec `json:"permissions"`

	// The user's secret name
	SecretName string `json:"secretName"`

	// A map of the docker images used. Maps image names to tags (versions).
	Images map[string]string `json:"images"`

	// Dbt project home path (code_server)
	// +optional
	DbtHome string `json:"dbtHome,omitempty"`

	// Code server profile name
	// +optional
	Profile string `json:"profile,omitempty"`

	// Clone git repository (code_server)
	// +optional
	CloneRepository string `json:"cloneRepository,omitempty"`

	// Disable code server
	// +optional
	CodeServerDisabled string `json:"codeServerDisabled,omitempty"`

	// Enable local airflow server as part of code server
	// +optional
	LocalAirflowEnabled string `json:"localAirflowEnabled,omitempty"`

	// Code server access
	// +optional
	CodeServerAccess string `json:"codeServerAccess,omitempty"`

	// Code server access
	// +optional
	CodeServerShareCode string `json:"codeServerShareCode,omitempty"`

	// A map of code server services.
	// +optional
	CodeServerExposures map[string]ServiceOptions `json:"codeServerExposures"`

	// Disable local dbt docs (code_server)
	// +optional
	LocalDbtDocsDisabled string `json:"localDbtDocsDisabled,omitempty"`

	// Disable dbt sync server (code_server)
	// +optional
	DbtSyncServerDisabled string `json:"dbtSyncServerDisabled,omitempty"`

	// Restart annotation (code_server)
	// +optional
	CodeServerRestartedAt string `json:"codeServerRestartedAt,omitempty"`

	// A map of enabled services.
	Services map[string]ServiceOptions `json:"services"`

	// Environment variables for local airflow
	// +optional
	LocalAirflowEnvironment []NameValuePair `json:"localAirflowEnvironment,omitempty"`
}

type NameValuePair struct {
	Name  string `json:"name"`
	Value string `json:"value"`
}

func (u *UserSpec) Equals(v UserSpec) bool {
	/*
	 * NOTE NOTE NOTE: This must be edited when adding fields to the
	 * above structure or the operator won't pick up the changes.
	 */
	if u.Email != v.Email || u.Slug != v.Slug || u.DbtHome != v.DbtHome || u.Profile != v.Profile ||
		u.SecretName != v.SecretName || u.LocalDbtDocsDisabled != v.LocalDbtDocsDisabled ||
		u.DbtSyncServerDisabled != v.DbtSyncServerDisabled || u.CloneRepository != v.CloneRepository || u.CodeServerDisabled != v.CodeServerDisabled ||
		u.CodeServerAccess != v.CodeServerAccess || u.CodeServerShareCode != v.CodeServerShareCode || u.CodeServerRestartedAt != v.CodeServerRestartedAt ||
		u.LocalAirflowEnabled != v.LocalAirflowEnabled {
		return false
	}
	if len(u.Permissions) != len(v.Permissions) {
		return false
	}
	for i, up := range u.Permissions {
		vp := v.Permissions[i]
		if up != vp {
			return false
		}
	}
	if len(u.Images) != len(v.Images) {
		return false
	}
	for ik, ui := range u.Images {
		vi, exists := v.Images[ik]
		if !exists || ui != vi {
			return false
		}
	}
	if len(u.CodeServerExposures) != len(v.CodeServerExposures) {
		return false
	}
	for ik, us := range u.CodeServerExposures {
		vi, exists := v.CodeServerExposures[ik]
		if !exists || us["port"] != vi["port"] {
			return false
		}
	}

	// Check environment
	if len(u.LocalAirflowEnvironment) != len(v.LocalAirflowEnvironment) {
		return false
	}

	/*
	 * This assumes environment variables will always show up in the same
	 * order in the array.  However, because we are generating them
	 * programatically, that should always be the case (unless the array
	 * changes)
	 */
	for i, up := range u.LocalAirflowEnvironment {
		vp := v.LocalAirflowEnvironment[i]

		if up.Name != vp.Name || up.Value != vp.Value {
			return false
		}
	}

	return true
}

func (u *UserSpec) HasPermissionForService(serviceName string) bool {
	for _, permission := range u.Permissions {
		if permission.Service == serviceName {
			return true
		}
	}
	return false
}

func (u *UserSpec) CodeServerEnabled() bool {
	return u.CodeServerDisabled != "true"
}

func (u *UserSpec) IsLocalAirflowEnabled() bool {
	return u.LocalAirflowEnabled == "true"
}

// PermissionSpec defines the desired state of User permissions
type PermissionSpec struct {
	// Service prefix, i.e. "airbyte"
	Service string `json:"service"`

	// Resources, i.e. "/subpath, read https://www.pomerium.com/reference/#prefix"
	// +optional
	Path string `json:"path,omitempty"`
}

// UserStatus defines the observed state of User
type UserStatus struct {
}

//+kubebuilder:object:root=true
//+kubebuilder:subresource:status

// User is the Schema for the users API
type User struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   UserSpec   `json:"spec,omitempty"`
	Status UserStatus `json:"status,omitempty"`
}

//+kubebuilder:object:root=true

// UserList contains a list of User
type UserList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []User `json:"items"`
}

func init() {
	SchemeBuilder.Register(&User{}, &UserList{})
}
