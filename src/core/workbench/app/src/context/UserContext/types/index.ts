import { ConnectionTemplate } from '../../../features/global/types';
import { Account } from '../../AccountContext/types';

export type AirflowConfig = {
  dags_folder: string;
  yaml_dags_folder: string;
  dags_source: string;
  git_branch?: string;
  s3_sync?: S3DagSyncConfig;
  logs?: DagLogsConfig;
  resources?: AirflowResources;
  api_enabled?: boolean;
};

export interface AirflowResources {
  scheduler: ResourceConfig;
  triggerer: ResourceConfig;
  webserver: ResourceConfig;
  workers: ResourceConfig;
  statsd: ResourceConfig;
}

export interface ResourceConfig {
  requests: MemoryConfig;
  limits: MemoryConfig;
}

export interface MemoryConfig {
  cpu: string;
  memory: string;
}

export type S3DagSyncConfig = {
  path: string;
  access_key?: string;
  secret_key?: string;
  iam_role?: string;
};

export type DagLogsConfig = {
  external: boolean;
  backend?: string;
  s3_log_bucket?: string;
  access_key?: string;
  secret_key?: string;
  volume_handle?: string;
};

export type DbtDocsConfig = {
  git_branch: string;
};

export interface CodeServerConfig {
  resources: ResourceConfig;
}

export type EnvironmentIntegration = {
  id?: string;
  integration: string;
  type: string;
  service: string;
  is_notification?: boolean;
};

export type Precondition = {
  code: string;
  message: string;
};

export type ServiceStatus = {
  enabled: boolean;
  valid: boolean;
  unmet_preconditions?: Precondition[];
};

export type Environment = {
  id: string;
  name: string;
  services: Record<string, ServiceStatus>;
  type: string;
  slug: string;
  created_at: string;
  project: string;
  service_credentials_count: number;
  dbt_home_path: string;
  dbt_profiles_dir: string;
  airflow_config: AirflowConfig;
  dbt_docs_config: DbtDocsConfig;
  code_server_config: CodeServerConfig;
  integrations: EnvironmentIntegration[];
  variables: EnvironmentVariables;
  release_profile: string;
  settings: any;
};

export type EnvironmentKeys = {
  id: string;
  slug: string;
  error?: string;
  airflow_api_url?: string;
  tokens?: string[];
  new_token?: string;
};

export type Repository = {
  git_url: string;
  url: string;
  provider: string;
};

export type DeployCredentials = {
  git_username: string;
  git_password?: string;
  azure_tenant?: string;
};

export type Project = {
  clone_strategy: string;
  id: string;
  name: string;
  release_branch: string;
  slug: string;
  settings: any;
  ci_home_url: string;
  ci_provider: string;
  deploy_credentials: DeployCredentials;
  deploy_key: string;
  azure_deploy_key: string;
  public_ssh_key?: string;
  public_azure_key?: string;
  repository: Repository;
  environments: Environment[];
  connection_templates: ConnectionTemplate[];
  validated_at: string;
  variables: EnvironmentVariables;
  release_branch_protected: boolean;
  secrets_backend: string;
  secrets_backend_config: SecretsBackendConfig;
  secrets_secondary_backend: string;
  secrets_secondary_backend_config: any;
};

export type ProjectKeys = {
  id: string;
  slug: string;
  error?: string;
  tokens?: string[];
  new_token?: string;
  dbt_api_url?: string;
};

export type Features = {
  user_profile_delete_account: boolean;
  user_profile_change_name: boolean;
  user_profile_change_ssh_keys: boolean;
  user_profile_change_ssl_keys: boolean;
  user_profile_change_credentials: boolean;
  accounts_signup: boolean;
  admin_account: boolean;
  admin_groups: boolean;
  admin_create_groups: boolean;
  admin_invitations: boolean;
  admin_users: boolean;
  admin_projects: boolean;
  admin_environments: boolean;
  admin_billing: boolean;
  admin_connections: boolean;
  admin_service_credentials: boolean;
  admin_integrations: boolean;
  admin_secrets: boolean;
  admin_profiles: boolean;
  admin_code_server_environment_variables: boolean;
  admin_env_code_server_mem_and_cpu_resources: boolean;
  admin_env_airflow_mem_and_cpu_resources: boolean;
  stop_codeserver_on_inactivity: boolean;
  shareable_codeserver: boolean;
  codeserver_exposures: boolean;
  codeserver_restart: boolean;
  observability_stack: boolean;
  select_minio_logs: boolean;
  show_get_started_banner: boolean;
  local_airflow: boolean;
};

export type UserEnvironment = {
  id: string;
  code_server_access: string;
  services: any;
  share_links: Record<string, string>;
  variables: EnvironmentVariables;
  env_slug: string;
  env_name: string;
  project_name: string;
};

export type User = {
  name: string;
  email: string;
  email_username: string;
  slug: string;
  avatar: string;
  permissions: string[];
  projects: Project[];
  trial_accounts: number;
  features: Features;
  user_environments: UserEnvironment[];
  env_account?: string;
  release: string;
  customer_portal?: string;
  has_license: boolean;
  has_dynamic_blob_storage_provisioning: boolean;
  has_dynamic_network_filesystem_provisioning: boolean;
  setup_enabled: boolean | null;
};

export type Template = {
  id: string;
  name: string;
  description: string;
  context_type: string;
  format: string;
};

export interface IUserContext {
  currentUser: User | undefined;
  setCurrentUser: (user: User | undefined) => void;
}

export type ProfileFile = {
  mount_path: string;
  template: Template;
  override_existent: boolean;
  execute: boolean;
};

export type Profile = {
  id: string;
  name: string;
  slug: string;
  account: Account;
  dbt_sync: boolean;
  dbt_local_docs: boolean;
  mount_ssl_keys: boolean;
  mount_ssh_keys: boolean;
  mount_api_token: boolean;
  clone_repository: boolean;
  files_from?: Profile;
  files: ProfileFile[];
  profile_files_count: number;
  is_system_profile: boolean;
};

export type EnvironmentVariableValue = {
  value: string;
  delete: boolean;
};

export type EnvironmentVariablesDeletable = {
  [key: string]: EnvironmentVariableValue;
};

export type EnvironmentVariables = {
  [key: string]: string;
};

export type SecretsBackendConfig = {
  [key: string]: string;
};
