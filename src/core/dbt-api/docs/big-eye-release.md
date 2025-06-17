# Playbook for releasing dbt-api

Once BigEye is ready to fetch our data through a dbt cloud-like API, we need to do the following steps to enable them:

## Enabling dbt-api in Production
First, we need to start the `dbt-api` pod in the production cluster.

### Sync the Secrets

In the cluster environment, sync the secrets with `./cli sync_secrets`. Make sure that you have the `core-dbt-api.env` file in the `config/{cluster_domain}/secrets` folder.

If needed, create a new S3 bucket to use for uploading the manifests of the production cluster. There's a development one in 1Password.

Next, set `dbt-api` to use S3 instead of Minio for uploading the manifests. Set the following environment variables in the `core-dbt-api.env`:

```
STORAGE_ADAPTER=s3
S3_BUCKET_NAME=fill_in
S3_ACCESS_KEY=fill_in
S3_SECRET_ACCESS_KEY=fill_in
S3_REGION=fill_in
```

Also, double-check the `DB_*` and `DATACOVES_DB_*` environment variables. They need to point to the same Postgres database that Datacoves is using. All database env variables should be the same except for the `DB_NAME` and `DATACOVES_DB_NAME` ones.

### Enabling dbt-api

To start the `dbt-api` pod, change the `cluster-params.yml` like this:

```
enable_dbt_api: true
expose_dbt_api: true
```

Then run `./cli.py setup_core`. This will start the `dbt-api` pod and expose it through a service to the URL

```
dbt.{cluster_domain}
```

You can test that `dbt-api` is running by checking out the API docs at:

```
dbt.{cluster_domain}/api/v2/swaggerui
```

## Uploading Manifests

### Checking the `dbt-coves` version

Before starting Airflow, make sure that you've released a new version of `dbt-coves` after [this PR](https://github.com/datacoves/dbt-coves/pull/427) was merged. Make sure that Airflow is started with that `dbt-coves` version. Otherwise, it won't upload the manifests to `dbt-api`.

### Checking network policies

We're currently blocking network requests between an environment and the `core` namespace. Make sure that you have a network policy in place that allows HTTP requests from the Airflow worker or namespace to `dbt-api`. Otherwise, your manifest upload will fail with a timeout.

### Checking the datacoves version

Make sure that you've created a new release of `datacoves` after [this PR](https://github.com/datacoves/datacoves/pull/413) was merged. Otherwise, you can't enable the manifest upload.

### Finally enabling the upload

To enable the manifest upload for all DAGRuns in an environment, open the Environment in the Admin Panel and set `upload_manifest: true` in the `Airflow Config`. Hit `Sync cluster` afterwards to sync the new settings. Datacoves will now add three new environment variables to the Airflow worker which `dbt-coves` will check after every `dbt-coves dbt` command. If the command created a `manifest.json`, it will upload it to `dbt-api`.

## Giving access to BigEye

At this point, we offer all records for an account through the API at `dbt.{cluster_domain}/api/v2`. All BigEye needs is a `Token`` per `Account`.

### Creating a Token

To create a Token for an account, create a shell connection to `dbt-api` with `./cli pod_sh dbt-api` and run `./run.sh shell`. Now, you're inside the production `dbt-api` pod.

First, you need the `account.id` for which you want to create a Token. The `id` is the integer id you can see in the Admin Panel when you go to `Accounts`. The first account has the id `1` and so on. You can also find the account id if you open the Account for editing in the Admin panel and look at the URL:

```
# The "account/1" part in the URL means this account has the id: 1
https://api.datacoveslocal.com/panel/users/account/1/change/
```

Now, you can create a new Token with this command from inside the shell:

```
iex> Jade.Auth.TokenRepo.create(%{account_id: ACCOUNT_ID})
# This will give you such a result:
{:ok,
 %Jade.Auth.Token{
   __meta__: #Ecto.Schema.Metadata<:loaded, "tokens">,
   id: 1,
   account_id: 1,
   key: "long-string-here",
   key_hash: "another-long-string-here",
   inserted_at: ~U[2023-12-22 17:16:16Z],
   updated_at: ~U[2023-12-22 17:16:16Z]
 }}
```

The `key` here is your API Token. Give this to BigEye. They can only query records for account of the Token, so in this case, they can only query for records for the account `1`. If they need more than one account, they need to use more than one token.

**Watch out: You will never see the token again!**

Make sure to copy the `key` after you've created it. Only a hash of the token is stored and used for comparison.

### Using the Token

BigEye (or any other customer) must provide the token `key` from above as a `Bearer` token in their HTTP Request.


### Deleting a Token

To delete a token, simply run these commands:

```elixir
{:ok, token} = Jade.Auth.TokenRepo.get_by_account_id(ACCOUNT_ID)
# Then
{:ok, _token} = Jade.Auth.TokenRepo.delete(token)
```

This will delete the token and the next HTTP request won't be authorized anymore.