# How to set up Snowflake Key-Based Auth for CI Service Accounts

## Overview

Snowflake service accounts must be set up with key-based auth as password based auth is being deprecated. These accounts are typically used for CI/CD.

## Creating key pair

Outside of Snowflake create a key-pair following the information on the [Snowflake documentation](https://docs.snowflake.com/en/user-guide/key-pair-auth)

First Generate the Private Key
`openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt`

From the Private Key, generate the Public Key
`openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub`

Store the private and public keys somewhere secure.

## Configure the service user in Snowflake

Print out the public key and add to Snowflake

`cat rsa_key.pub`

This will show your public kay which will replace `<your public key>` below.

>[!NOTE] Exclude the --BEGIN-- and --END-- lines from the public key

`ALTER USER SVC_GITHUB_ACTIONS SET RSA_PUBLIC_KEY='<your public key>';`

## Verify the public key was set correctly

Run the following command in Snowflake
```
DESC USER SVC_GITHUB_ACTIONS;
SELECT SUBSTR((SELECT "value" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
  WHERE "property" = 'RSA_PUBLIC_KEY_FP'), LEN('SHA256:') + 1);
```

Run the following command in the terminal
`openssl rsa -pubin -in rsa_key.pub -outform DER | openssl dgst -sha256 -binary | openssl enc -base64`

Compare both outputs. If both outputs match, the user correctly configured their public key.

## Configure Github Actions

In Github, you must configure the Private Key. To do this visit the settings page of your repo. In the `Security` section click `Secrets and Variables` then select `Actions`.

In the  `Secrets` tab add a `New Repository Secret`.
Give it a `Name` like `DATACOVES__MAIN__PRIVATE_KEY`

Print the Private Key generated earlier.
`cat rsa_key.p8`
 
>[!NOTE] Exclude the --BEGIN-- and --END-- lines from the private key

Copy the content and of the private key and paste it as the value for the Github `Secret` and `Add Secret`.
 
## Configure the dbt profile

Update the profile you use for CI/CD. Typically this is located in `automate/dbt/profiles.yml` if using the recommended Datacoves location.

It should look something like this:

```yaml
default:
  target: default_target
  outputs:
    default_target:
      type: snowflake
      threads: 16
      client_session_keep_alive: true

      account: "{{ env_var('DATACOVES__MAIN__ACCOUNT') }}"
      database: "{{ env_var('DATACOVES__MAIN__DATABASE') }}"
      schema: "{{ env_var('DATACOVES__MAIN__SCHEMA') }}"
      user: "{{ env_var('DATACOVES__MAIN__USER') }}"
      private_key: "{{ env_var('DATACOVES__MAIN__PRIVATE_KEY') }}"
      role: "{{ env_var('DATACOVES__MAIN__ROLE') }}"
      warehouse: "{{ env_var('DATACOVES__MAIN__WAREHOUSE') }}"
```  