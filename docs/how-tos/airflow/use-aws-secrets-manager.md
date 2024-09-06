# How to use AWS Secrets Manager to store Airflow variables and connections

Datacoves implements the Airflow Secrets Backend interface supporting different type of secrets managers,
including AWS Secrets Manager, among others.

Secrets backends are configured at project level, it means that you could use a different Secrets Manager for each project.

To configure AWS Secrets Manager as the default secrets provider, you'll need:
1) An IAM user created on AWS with permissions to access them and
2) To change your project settings, selecting `AWS Secrets Manager` in the `Backend` field

## Create an IAM user with permissions to manage secrets

On AWS, create an IAM User with an attached policy like this one:

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

>[!NOTE]Note that this policy is granting access **only** to secrets created with the prefix `datacoves/*`, if you need to 
share any existing secret with Datacoves services you need to recreate it using [Datacoves Secrets Admin](how-tos/datacoves/how_to_secrets)

Once you created the IAM user and the policy was correctyly attached, create an access key keeping it safe to use it in the next step.

## Configure access to AWS Secrets Manager on the project settings page

Navigate to the Projects Admin page and edit the desired project. On the `backend` field select `AWS Secrets Manager`

![Project Secrets Backend](./assets/edit_project_secrets_backend.png)

This secrets backend requires the following fields:

- **Region Code** This is the region were the Secrets Manager is running, i.e. us-east-1, us-west-1, etc. Find a complete list [here](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html)
- **Access Key ID** Paste here the Access Key ID you configured earlier
- **Secret Access Key** Paste here the Secret Access Key attachted to the IAM User configured earlier
