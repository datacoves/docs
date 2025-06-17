## Configuring datacoves

Requirements: Access to a datacoves configuration git repo and being in it's git secret keyring.

First pull the latest changes and reveal the git secrets.

```bash
git checkout main
git pull
git secret reveal -f
```

I've marked with `TODO` the values that need to be filled in:

- Airflow DB connection in: `environments/dev123/airflow.secret.yaml`
- Airflow EFS volume_handle (fs id) in: `environments/dev123/airflow.secret.yaml`
- Datacoves api DB host (`DB_HOST`) and password (`DB_PASS`) in `secrets/core-api.env`
- PING_CLIENT_ID and PING_CLIENT_SECRET in `secrets/core-api.env`

After editing those files to add the required values commit the changes with:

```bash
git secret hide
git diff # Review your changes, all sensitive data should be encrypted.
git add .
git commit -m 'Updated secrets.'
git push
```
