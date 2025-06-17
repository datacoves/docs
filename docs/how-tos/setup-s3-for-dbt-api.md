# Create a S3 bucket for dbt api artifacts

## Create bucket on AWS console

- Create an S3 bucket.
- Choose a bucket name, we suggest using <cluster_id>_dbt_api where <cluster_id> could be `ensemble`, `ensembletest`, etc.
- Create an IAM user with a policy to access the bucket, like the one below,
  replacing `{your_bucket_name}` with your bucket's name.
- Create an access key for the user. Share it with the Datacoves team.

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion"
      ],
      "Resource": "arn:aws:s3:::{your_bucket_name}/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::{your_bucket_name}"
    }
  ]
}
```

## Configure Datacoves accordingly

For the cluster being configured, set the following environment variables in the `core-dbt-api.env` file:

```
STORAGE_ADAPTER=s3
S3_BUCKET_NAME=fill_in
S3_ACCESS_KEY=fill_in
S3_SECRET_ACCESS_KEY=fill_in
S3_REGION=fill_in
```