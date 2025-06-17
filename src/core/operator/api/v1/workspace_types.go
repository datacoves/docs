package v1

import (
	"fmt"
	"strings"

	core "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// NOTE: Run "make" to regenerate code after modifying this file.

// WorkspaceSpec defines the desired state of Workspace
type WorkspaceSpec struct {
	// The workspace's account name.
	Account string `json:"account"`

	// The workspace's project name.
	Project string `json:"project"`

	// Is account suspended?
	// +optional
	AccountSuspended string `json:"accountSuspended,omitempty"`

	// The domain of the cluster. Used to derive ingress rules.
	ClusterDomain string `json:"clusterDomain"`

	// The name of a cert-manager issuer to put on ingress annotations, for SSL.
	// +optional
	CertManagerIssuer string `json:"certManagerIssuer,omitempty"`

	// An URL to put on ingress annotations so that external-dns creates DNS records.
	// +optional
	ExternalDnsUrl string `json:"externalDnsUrl,omitempty"`

	// The IP of the internal-dns so that network policies allow communication with it.
	// +optional
	InternalDnsIp string `json:"internalDnsIp,omitempty"`

	// The cluster internal IP
	// +optional
	InternalIp string `json:"internalIp,omitempty"`

	// The cluster external IP
	// +optional
	ExternalIp string `json:"externalIp,omitempty"`

	// The IP of the internal-dns so that network policies allow communication with it.
	// +optional
	ClusterApiServerIps ClusterApiServerIps `json:"clusterApiServerIps,omitempty"`

	// The IP of the internal-dns so that network policies allow communication with it.
	// +optional
	InternalDbClusterIpRange string `json:"internalDbClusterIpRange,omitempty"`

	// The docker image registry to pull images from. Empty implies dockerhub.
	ImageRegistry string `json:"imageRegistry"`

	// +optional
	ImagePullSecret string `json:"imagePullSecret,omitempty"`

	// A map of the docker images used. Maps image names to tags (versions).
	Images map[string]string `json:"images"`

	// Release profile name
	ReleaseProfile string `json:"releaseProfile,omitempty"`

	// A map of enabled services.
	Services map[string]ServiceOptions `json:"services"`

	// A map of enabled internal services.
	InternalServices map[string]ServiceOptions `json:"internalServices"`

	// A map of service helm charts configs
	Charts map[string]ChartConfigs `json:"charts"`

	// The workspace's users.
	Users []UserSpec `json:"users"`

	// The oidc token attribute used to identify the user
	OidcUserId string `json:"oidcUserId"`

	// Map the name of a config to the name of a resource containing its current value.
	Configs map[string]string `json:"configs"`

	// The ssh git url to the project repository
	// +optional
	SshGitRepo string `json:"sshGitRepo,omitempty"`

	// The http git url to the project repository
	// +optional
	HttpGitRepo string `json:"httpGitRepo,omitempty"`

	// The git clone strategy, could be either 'ssh_clone' or 'http_clone'
	GitCloneStrategy string `json:"gitCloneStrategy"`

	// Clone git repository (code_server)
	// +optional
	CloneRepository string `json:"cloneRepository,omitempty"`

	// Runs python web apps in development mode (code_server)
	// +optional
	DontUseWsgi string `json:"dontUseWsgi,omitempty"`

	// If true, we will use the node local DNS for all pods.  The cluster
	// must be installed with the install_node_local_dns option set to true
	// in the cluster-params yaml
	// +optional
	NodeLocalDnsEnabled string `json:"nodeLocalDnsEnabled,omitempty"`

	// Dbt project home path (code_server)
	// +optional
	DbtHome string `json:"dbtHome,omitempty"`

	// Dbt docs git branch (dbt_docs)
	// +optional
	DbtDocsGitBranch string `json:"dbtDocsGitBranch,omitempty"`

	// Dbt docs AskPass URL if using Azure (dbt_docs)
	// +optional
	DbtDocsAskpassUrl string `json:"dbtDocsAskpassUrl,omitempty"`

	// Disable local dbt docs (code_server)
	// +optional
	LocalDbtDocsDisabled string `json:"localDbtDocsDisabled,omitempty"`

	// Disable dbt sync server (code_server)
	// +optional
	DbtSyncServerDisabled string `json:"dbtSyncServerDisabled,omitempty"`

	// +optional
	ResourceRequirements map[string]core.ResourceRequirements `json:"resourceRequirements,omitempty"`
}

type ServiceOptions map[string]string

type ChartConfigs map[string]string

// WorkspaceStatus defines the observed state of Workspace
type WorkspaceStatus struct {
}

//+kubebuilder:object:root=true
//+kubebuilder:subresource:status

// Workspace is the Schema for the workspaces API
type Workspace struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   WorkspaceSpec   `json:"spec,omitempty"`
	Status WorkspaceStatus `json:"status,omitempty"`
}

/*
 * This adds DNS spec to a given PodSpec if it is necessary (i.e if
 * Workspace.WorkspaceSpec.NodeLocalDnsEnabled is True
 */
func (w *Workspace) AddDnsToPodSpecIfNeeded(spec *core.PodSpec) {
	if w.NodeLocalDnsEnabled() {
		spec.DNSPolicy = core.DNSNone
		spec.DNSConfig = &core.PodDNSConfig{
			Nameservers: []string{
				"169.254.20.25",
				"10.96.0.10",
			},
			Searches: []string{
				"core.svc.cluster.local",
				"svc.cluster.local",
				"cluster.local",
			},
			Options: []core.PodDNSConfigOption{
				{
					Name:  "ndots",
					Value: &[]string{"1"}[0],
				},
				{
					Name:  "attempts",
					Value: &[]string{"5"}[0],
				},
				{
					Name:  "timeout",
					Value: &[]string{"5"}[0],
				},
			},
		}
	}
}

func (w *Workspace) ImageName(img string) string {
	registry := w.Spec.ImageRegistry
	tag := "latest" // TODO: Might not want to fallback to latest.
	if t, found := w.Spec.Images[img]; found {
		tag = t
	}
	if registry != "" {
		registry += "/"
	}
	return fmt.Sprintf("%s%s:%s", registry, img, tag)
}

/*
 * Finds a "profile image". Given an img like "path/name", a profile image will
 * have the form "path/pi{profile_id}-name". This function assumes there's only
 * one such image in w.Images (workspace.py will make it so). If there's more
 * it will return the first it finds. We don't know and we don't care what the
 * profile id is from the operator.
 *
 * If it doesn't find it in the profile images, it will use the ReleaseProfile
 * string instead, in such a fashion:
 *
 * "path/name-{ReleaseProfile}" where release profile will likely be
 * something such as "dbt-snowflake"
 *
 * optional_suffix is an optional parameter; if provided, it will be appeneded
 * to the end of the profile name.  It is intended for use with local versions
 * of things, i.e airflow-airflow-dbt-snowflake-local, etc.
 */
func (w *Workspace) ProfileImageName(img string, optional_suffix ...string) string {
	prefix := "pi"
	suffix := ""
	contains := "-" + img

	if len(optional_suffix) > 0 {
		suffix = "-" + optional_suffix[0]
	}

	if iSlash := strings.LastIndexByte(img, '/'); iSlash >= 0 {
		prefix = img[:iSlash] + "/pi"
		contains = "-" + img[iSlash+1:] + suffix
	}
	registry := w.Spec.ImageRegistry
	tag := ""
	for imageName, imageTag := range w.Spec.Images {
		if !strings.Contains(imageName, contains) || !strings.HasPrefix(imageName, prefix) {
			continue
		}
		// TODO: Check that the remaining bit is numeric. Assuming it for now.
		img, tag = imageName, imageTag
		break
	}
	if tag == "" {
		// Not found, fallback.
		return w.ImageName(img + "-" + w.Spec.ReleaseProfile + suffix)
	}
	if registry != "" {
		registry += "/"
	}
	return fmt.Sprintf("%s%s:%s", registry, img, tag)
}

func (w *Workspace) WorkbenchDomain() string {
	return fmt.Sprintf("%s.%s", w.Name, w.Spec.ClusterDomain)
}

func (w *Workspace) ServiceEnabled(serviceName string) bool {
	// built-ins, are never disabled so users can still load the environment's workbench
	if serviceName == "pomerium" || serviceName == "workbench" {
		return true
	}
	if w.Spec.AccountSuspended == "true" {
		return false
	}
	options, found := w.Spec.Services[serviceName]
	return found && options["enabled"] != "false" && options["valid"] != "false"
}

func (w *Workspace) InternalServiceEnabled(serviceName string) bool {
	if w.Spec.AccountSuspended == "true" {
		return false
	}
	options, found := w.Spec.InternalServices[serviceName]
	return found && options["enabled"] != "false" && options["valid"] != "false"
}

func (w *Workspace) NodeLocalDnsEnabled() bool {
	return w.Spec.NodeLocalDnsEnabled == "true"
}

func (w *Workspace) DontUseWsgi() bool {
	return w.Spec.DontUseWsgi == "true"
}

func (w *Workspace) LocalDbtDocs() bool {
	return w.Spec.LocalDbtDocsDisabled != "true"
}

func (w *Workspace) DbtSync() bool {
	return w.Spec.DbtSyncServerDisabled != "true"
}

func (w *Workspace) HPA() bool {
	return len(w.Spec.ResourceRequirements) > 0
}

//+kubebuilder:object:root=true

// WorkspaceList contains a list of Workspace
type WorkspaceList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []Workspace `json:"items"`
}

func init() {
	SchemeBuilder.Register(&Workspace{}, &WorkspaceList{})
}

// NOTE: Run "make" to regenerate code after modifying this file.

// ApiServerSpec: kubectl get endpoints --namespace default kubernetes
type ClusterApiServerIps struct {
	// Kubernates api server ips.
	Ips []string `json:"ips"`

	// Kubernates api server port.
	Ports []int32 `json:"ports"`
}
