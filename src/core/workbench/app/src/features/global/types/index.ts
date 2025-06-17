export type AccountSetupPayload = {
  account_name: string;
  project_name: string;
  release_branch: string;
  development_key_id: string;
  services: Services;
  connection: SetupConnection;
  repository: Repository;
  environment_configuration: EnvironmentConfiguration;
  project_settings: ProjectSettings;
};

type Services = {
  airbyte: boolean;
  superset: boolean;
  airflow: boolean;
};

type ProjectSettings = {
  dbt_profile?: string;
};

type EnvironmentConfiguration = {
  dbt_home_path?: string;
  airflow_config?: AirflowConfig;
};

type AirflowConfig = {
  dags_folder: string;
  yaml_dags_folder: string;
};

type SetupConnection = {
  type: string;
  connection_details: ConnectionDetails;
};

type ConnectionDetails = { [key: string]: any };

type Repository = {
  git_url: string;
};

export type SSHKey = {
  id: string;
  ssh_key: string;
};

export type SSLKey = {
  id: string;
  ssl_key: string;
};

export type ConnectionType = {
  id: string;
  slug: string;
  name: string;
};

export type ConnectionTemplate = {
  id: string;
  type: string;
  type_slug: string;
  name: string;
  connection_details: ConnDetails;
  for_users: boolean;
  project: string;
  user_credentials_count: number;
  service_credentials_count: number;
  connection_user: string;
  connection_user_template: string;
  default_username: string;
};

type ConnectionWithType = {
  type: ConnectionType;
};

// Resolved and Readonly connection template
export type RConnectionTemplate = ConnectionTemplate & ConnectionWithType;

type ConnDetails = {
  role: string;
  account: string;
  database: string;
  warehouse: string;
  host: string;
  http_path: string;
  schema: string;
  dataset: string;
  mfa_protected: boolean;
};

export type UserCredential = {
  id: string;
  name: string;
  user: string;
  environment: string;
  connection_template: string;
  connection_overrides: ConnectionOverrides;
  ssl_key?: string;
  validated_at: string;
};

export type ServiceCredential = {
  id: string;
  name: string;
  environment: string;
  connection_template: string;
  connection_overrides: ConnectionOverrides;
  ssl_key?: string;
  public_ssl_key?: string;
  service: string;
  validated_at: string;
  delivery_mode: string;
};

type ConnectionOverrides = {
  role: string;
  account: string;
  database: string;
  warehouse: string;
  user: string;
  password?: string;
  schema?: string;
  host?: string;
  catalog?: string;
  http_path?: string;
  token?: string;
  keyfile_json?: string;
  dataset?: string;
};

export type UserRepository = {
  id: string;
  url: string;
  validated_at: string;
};

export type UserSSHKey = {
  id: string;
  key_type: string;
  public: string;
  repos: UserRepository[];
};

export type UserSSLKey = {
  id: string;
  key_type: string;
  public: string;
};

export type Integration = {
  id: string;
  type: string;
  name: string;
  settings: any;
  is_notification: boolean;
  is_default: boolean;
};

export type Secret = {
  id: string;
  slug: string;
  tags: string[];
  description: string;
  sharing_scope: string;
  project: string;
  environment: string;
  users: boolean;
  services: boolean;
  created_by_name: string;
  created_by_email: string;
  value_format: string;
  value: { [key: string]: string | object };
  accessed_at: string;
  secrets_backend_error?: string;
  backend: string;
  is_system: boolean;
};
