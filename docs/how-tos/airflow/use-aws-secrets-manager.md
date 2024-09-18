# How to use AWS Secrets Manager to store Airflow variables and connections

Datacoves implements the Airflow Secrets Backend Interface to support different types of secrets managers
including AWS Secrets Manager.

Secrets backends are configured at the project level, this means that you can use a different Secrets Manager for each project.

To configure AWS Secrets Manager as the default secrets provider, you'll need:

1) Create an IAM user with permissions to manage secrets
2) Configure access to AWS Secrets Manager on the project settings page

Please follow the how to below to achieve these requirements.

## Create an IAM user with permissions to manage secrets

**Step 1:** On AWS, create an IAM User with an attached policy like this one:

```json
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Effect": "Allow",
			"Action": [
				"secretsmanager:GetSecretValue",
				"secretsmanager:DescribeSecret",
				"secretsmanager:PutSecretValue",
				"secretsmanager:CreateSecret",
				"secretsmanager:DeleteSecret",
				"secretsmanager:UpdateSecret",
				"secretsmanager:ListSecrets"
			],
			"Resource": "arn:aws:secretsmanager:*:*:secret:datacoves/*"
		}
	]
}
```

>[!NOTE]This policy is granting access **only** to secrets created with the prefix `datacoves/*`, if you need to 
share any existing secret with Datacoves services you need to recreate it using [Datacoves Secrets Admin](how-tos/datacoves/how_to_secrets)

**Step 2:** Once you created the IAM user and the policy was correctly attached, create an access key and store it somewhere safe. You will be using it in the following step.

## Configure access to AWS Secrets Manager on the project settings page

**Step 1:** Navigate to the Projects Admin page and click on the edit icon for the desired project.

![Project](assets/menu_projects.gif)

**Step 2:** Scroll down to the `backend` field select `AWS Secrets Manager`

![Project Secrets Backend](./assets/edit_project_secrets_backend.png)

**This secrets backend will require the following fields:**

- **Region Code** This is the region were the Secrets Manager is running, i.e. `us-east-1`, `us-west-1`, etc. Find a complete list [here](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html)
- **Access Key ID** The Access Key ID you configured earlier
- **Secret Access Key** The Secret Access Key attached to the IAM User configured earlier
