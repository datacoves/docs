defmodule JadeWeb.OpenApi.Schemas do
  # Accounts

  defmodule Account do
    use JadeWeb, :openapi_schema

    OpenApiSpex.schema(%{
      description: "An account",
      type: :object,
      additionalProperties: false,
      properties: %{
        id: Generic.integer(),
        name: Generic.string(),
        state: Generic.integer(),
        plan: Generic.string(),
        pending_cancel: Generic.boolean(),
        run_slots: Generic.integer(),
        developer_seats: Generic.integer(),
        it_seats: Generic.integer(),
        read_only_seats: Generic.integer(),
        pod_memory_request_mebibytes: Generic.integer(),
        run_duration_limit_seconds: Generic.integer(),
        queue_limit: Generic.integer(),
        stripe_customer_id: Generic.integer(),
        metronome_customer_id: Generic.integer(),
        salesforce_customer_id: Generic.integer(),
        third_party_billing: Generic.boolean(),
        billing_email_address: Generic.string(),
        locked: Generic.boolean(),
        lock_reason: Generic.string(),
        lock_cause: Generic.string(),
        develop_file_system: Generic.boolean(),
        unlocked_at: Generic.datetime(),
        unlock_if_subscription_renewed: Generic.boolean(),
        enterprise_authentication_method: Generic.string(),
        enterprise_login_slug: Generic.string(),
        enterprise_unique_identifier: Generic.string(),
        business_critical: Generic.boolean(),
        created_at: Generic.datetime(),
        updated_at: Generic.datetime(),
        starter_repo_url: Generic.string(),
        git_auth_level: Generic.string(),
        identifier: Generic.string(),
        trial_end_date: Generic.datetime(),
        static_subdomain: Generic.string(),
        run_locked_until: Generic.datetime(),
        docs_job_id: Generic.integer(),
        freshness_job_id: Generic.integer()
      }
    })
  end

  defmodule ShowAccountResponse do
    use JadeWeb, :openapi_schema

    alias JadeWeb.OpenApi.Schemas.Account

    OpenApiSpex.schema(%{
      type: :object,
      properties: %{
        data: Account
      }
    })
  end

  # Projects

  defmodule Project do
    use JadeWeb, :openapi_schema

    OpenApiSpex.schema(%{
      description: "An account's project",
      type: :object,
      additionalProperties: false,
      properties: %{
        id: Generic.integer(nullable: false),
        name: Generic.string(),
        slug: Generic.string(),
        account_id: Generic.integer(nullable: false),
        connection_id: Generic.integer(),
        repository_id: Generic.integer(),
        semantic_layer_id: Generic.integer(),
        integration_entity_id: Generic.integer(),
        skipped_setup: Generic.boolean(),
        state: Generic.integer(),
        dbt_project_subdirectory: Generic.string(),
        docs_job_id: Generic.integer(),
        freshness_job_id: Generic.integer(),
        created_at: Generic.datetime(),
        updated_at: Generic.datetime()
      }
    })
  end

  defmodule ListProjectsResponse do
    use JadeWeb, :openapi_schema

    alias JadeWeb.OpenApi.Schemas.Project

    OpenApiSpex.schema(%{
      type: :object,
      properties: %{
        data: Generic.array_of(Project)
      }
    })
  end

  defmodule ShowProjectResponse do
    use JadeWeb, :openapi_schema

    alias JadeWeb.OpenApi.Schemas.Project

    OpenApiSpex.schema(%{
      type: :object,
      properties: %{
        data: Project
      }
    })
  end

  # Environments

  defmodule Environment do
    use JadeWeb, :openapi_schema

    OpenApiSpex.schema(%{
      description: "An account's environment",
      type: :object,
      additionalProperties: false,
      properties: %{
        id: Generic.integer(nullable: false),
        project_id: Generic.integer(nullable: false),
        account_id: Generic.integer(),
        connection_id: Generic.integer(),
        credentials_id: Generic.integer(),
        created_by_id: Generic.integer(),
        extended_attributes_id: Generic.integer(),
        repository_id: Generic.integer(),
        name: Generic.string(),
        slug: Generic.string(),
        dbt_project_subdirectory: Generic.string(),
        use_custom_branch: Generic.boolean(),
        custom_branch: Generic.string(),
        dbt_version: Generic.string(),
        raw_dbt_version: Generic.string(),
        supports_docs: Generic.boolean(),
        state: Generic.integer(),
        custom_environment_variables: Generic.string(),
        created_at: Generic.datetime(),
        updated_at: Generic.datetime()
      }
    })
  end

  defmodule ListEnvironmentsResponse do
    use JadeWeb, :openapi_schema

    alias JadeWeb.OpenApi.Schemas.Environment

    OpenApiSpex.schema(%{
      type: :object,
      properties: %{
        data: Generic.array_of(Environment)
      }
    })
  end

  defmodule ShowEnvironmentResponse do
    use JadeWeb, :openapi_schema

    alias JadeWeb.OpenApi.Schemas.Environment

    OpenApiSpex.schema(%{
      type: :object,
      properties: %{
        data: Environment
      }
    })
  end

  # Job Runs

  defmodule JobRun do
    use JadeWeb, :openapi_schema

    OpenApiSpex.schema(%{
      description: "A Run of a Job",
      type: :object,
      additionalProperties: false,
      properties: %{
        id: Generic.integer(),
        dbt_job_run_ext_id: Generic.integer(),
        job_id: Generic.integer(),
        dag_id: Generic.string(),
        dag_run_id: Generic.integer(),
        dag_run_run_id: Generic.string(),
        trigger_id: Generic.integer(),
        environment_id: Generic.integer(),
        environment_slug: Generic.string(),
        account_id: Generic.integer(),
        project_id: Generic.integer(),
        job_definition_id: Generic.string(),
        status: Generic.integer(description: "1: Success. 2: Error. 3: Queued. 5: Running."),
        dbt_version: Generic.string(),
        git_branch: Generic.string(),
        git_sha: Generic.string(),
        status_message: Generic.string(),
        owner_thread_id: Generic.string(),
        executed_by_thread_id: Generic.string(),
        deferring_run_id: Generic.integer(),
        artifacts_saved: Generic.boolean(),
        artifact_s3_path: Generic.string(),
        has_docs_generated: Generic.boolean(),
        has_sources_generated: Generic.boolean(),
        notifications_sent: Generic.boolean(),
        blocked_by: Generic.array_of(Generic.integer()),
        scribe_enabled: Generic.boolean(),
        completed_at: Generic.datetime(),
        created_at: Generic.datetime(),
        updated_at: Generic.datetime(),
        queued_at: Generic.datetime(),
        dequeued_at: Generic.datetime(),
        started_at: Generic.datetime(),
        finished_at: Generic.datetime(),
        last_checked_at: Generic.datetime(),
        last_heartbeat_at: Generic.datetime(),
        should_start_at: Generic.datetime(),
        status_humanized: Generic.string(),
        in_progress: Generic.boolean(),
        is_complete: Generic.boolean(),
        is_success: Generic.boolean(),
        is_error: Generic.boolean(),
        is_cancelled: Generic.boolean(),
        is_running: Generic.boolean(),
        duration: Generic.integer(description: "The queued_at until finished_at duration in seconds."),
        queued_duration: Generic.integer(description: "The queued_at until started_at duration in seconds."),
        run_duration: Generic.integer(description: "The started_at until finished_at duration in seconds"),
        duration_humanized: Generic.string(),
        queued_duration_humanized: Generic.string(),
        run_duration_humanized: Generic.string(),
        created_at_humanized: Generic.string(),
        finished_at_humanized: Generic.string()
      }
    })
  end

  defmodule ListJobRunsResponse do
    use JadeWeb, :openapi_schema

    alias JadeWeb.OpenApi.Schemas.JobRun

    OpenApiSpex.schema(%{
      type: :object,
      properties: %{
        data: Generic.array_of(JobRun)
      }
    })
  end

  defmodule ShowJobRunResponse do
    use JadeWeb, :openapi_schema

    alias JadeWeb.OpenApi.Schemas.JobRun

    OpenApiSpex.schema(%{
      type: :object,
      properties: %{
        data: JobRun
      }
    })
  end

  # Jobs

  defmodule Job do
    use JadeWeb, :openapi_schema

    alias Jade.Jobs.Job

    OpenApiSpex.schema(%{
      description: "A Job of a Project",
      type: :object,
      additionalProperties: false,
      properties: %{
        id: Generic.integer(nullable: false),
        project_id: Generic.integer(),
        dbt_job_ext_id: Generic.integer(),
        environment_id: Generic.integer(),
        dag_id: Generic.string(),
        deferring_job_definition_id: Generic.integer(),
        deferring_environment_id: Generic.integer(),
        lifecycle_webhooks: Generic.boolean(),
        lifecycle_webhooks_url: Generic.string(),
        account_id: Generic.integer(),
        name: Generic.string(),
        description: Generic.string(),
        dbt_version: Generic.string(),
        raw_dbt_version: Generic.string(),
        triggers: Generic.enum(Job.valid_triggers()),
        created_at: Generic.datetime(),
        updated_at: Generic.datetime(),
        schedule: Generic.string(),
        settings: Generic.map(),
        execution: Generic.map(),
        state: Generic.integer(),
        generate_docs: Generic.boolean(),
        run_generate_sources: Generic.boolean(),
        most_recent_completed_run: Generic.integer(),
        most_recent_run: Generic.integer(),
        is_deferrable: Generic.boolean(),
        deactivated: Generic.boolean(),
        run_failure_count: Generic.integer(),
        job_type: Generic.string(),
        triggers_on_draft_pr: Generic.boolean(),
        most_recent_job_run: Generic.nullable(JobRun),
        most_recent_completed_job_run: Generic.nullable(JobRun)
      }
    })
  end

  defmodule ListJobsResponse do
    use JadeWeb, :openapi_schema

    alias JadeWeb.OpenApi.Schemas.Job

    OpenApiSpex.schema(%{
      type: :object,
      properties: %{
        data: Generic.array_of(Job)
      }
    })
  end

  defmodule ShowJobResponse do
    use JadeWeb, :openapi_schema

    alias JadeWeb.OpenApi.Schemas.Job

    OpenApiSpex.schema(%{
      type: :object,
      properties: %{
        data: Job
      }
    })
  end

  # File

  defmodule FileContent do
    use JadeWeb, :openapi_schema

    OpenApiSpex.schema(%{
      description: "A File content.",
      type: :string,
      format: :binary
    })
  end

  defmodule FileUpload do
    use JadeWeb, :openapi_schema

    OpenApiSpex.schema(%{
      description: "An upload of one multipart/form-data file.",
      type: :object,
      additionalProperties: false,
      properties: %{
        tag: Generic.string(),
        file: FileContent
      }
    })
  end

  defmodule MultipleFilesUpload do
    use JadeWeb, :openapi_schema

    OpenApiSpex.schema(%{
      description: "An upload of multiple multipart/form-data files.",
      type: :object,
      additionalProperties: true,
      properties: %{
        files: Generic.array_of(FileUpload)
      }
    })
  end

  defmodule OneOrMultipleFileUploads do
    use JadeWeb, :openapi_schema

    OpenApiSpex.schema(%{
      description: "An upload of one or multiple multipart/form-data files.",
      oneOf: [
        FileUpload,
        MultipleFilesUpload
      ]
    })
  end

  defmodule File do
    use JadeWeb, :openapi_schema

    OpenApiSpex.schema(%{
      description: "A Datacoves File.",
      type: :object,
      additionalProperties: false,
      properties: %{
        id: Generic.integer(nullable: false),
        tag: Generic.string(),
        filename: Generic.string(),
        environment_slug: Generic.string(),
        path: Generic.string(),
        inserted_at: Generic.datetime(),
        updated_at: Generic.datetime()
      }
    })
  end

  defmodule FileResponse do
    use JadeWeb, :openapi_schema

    alias JadeWeb.OpenApi.Schemas.File

    OpenApiSpex.schema(%{
      description: "A File response.",
      type: :object,
      properties: %{
        data: File
      }
    })
  end

  defmodule ListFilesResponse do
    use JadeWeb, :openapi_schema

    alias JadeWeb.OpenApi.Schemas.File

    OpenApiSpex.schema(%{
      description: "A list of Files response.",
      type: :object,
      properties: %{
        data: Generic.array_of(File)
      }
    })
  end

  defmodule FileOrFilesResponse do
    use JadeWeb, :openapi_schema

    alias JadeWeb.OpenApi.Schemas.FileResponse
    alias JadeWeb.OpenApi.Schemas.ListFilesResponse

    OpenApiSpex.schema(%{
      description: "A file or list of files response.",
      type: :object,
      properties: %{
        data: Generic.one_of(FileResponse, ListFilesResponse)
      }
    })
  end

  # Artifacts

  defmodule ShowArtifactResponse do
    use JadeWeb, :openapi_schema

    OpenApiSpex.schema(%{
      description: "An Artifact for a JobRun. Returns the artifact content only.",
      type: :object,
      additionalProperties: false,
      properties: %{
        data: FileContent
      }
    })
  end

  # Generic Responses

  defmodule SuccessResponse do
    use JadeWeb, :openapi_schema

    OpenApiSpex.schema(%{
      type: :string
    })
  end

  defmodule ErrorResponse do
    use JadeWeb, :openapi_schema

    OpenApiSpex.schema(%{
      type: :object,
      additionalProperties: false,
      properties: %{
        errors: %Schema{
          type: :object,
          properties: %{
            message: Generic.string(nullable: false)
          }
        }
      }
    })
  end

  # Pagination Parameters

  defmodule Pagination do
    def limit() do
      [
        in: :query,
        description: "Limits the number of items in the response.",
        type: :integer,
        example: 20
      ]
    end

    def offset() do
      [
        in: :query,
        description: "Offsets the primary key of the items in the response.",
        type: :integer,
        example: 20
      ]
    end
  end
end
