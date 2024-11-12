# Airflow API - Getting Started

The Airflow API can be enabled or disabled per environment in Datacoves.  The default will vary based on your particular account and installation.  You can determine if the API is available for a given environment by looking for the padlock icon on the environments screen:

![Environments Screen](assets/airflow-api-environments.png)

To turn airflow API on or off, you must contact Datacoves support.  Note that turning off Airflow API will also disable the Datacoves Secrets Manager, which relies on the Airflow API to operate.

Our implementation of the Airflow API uses JWT tokens. You can either use service account tokens which are generated through our UI, or you can use JWT tokens associated with a Datacoves user.  The former is better for cases such as automation but relies on the use of a refresh token which will expire after 30 days; the latter is better for cases where a developer needs to interact with airflow for a specific purpose or if access will be so infrequent that the use of a refresh token is not practical.

## Generating Tokens

### Service User Tokens

1. Go to your Datacoves Launchpad
2. Click Environments on the left-side menu.
3. Click the padlock as pictured above.
4. All the information you need to access the API is provided.

![Environment Keys Screen](assets/airflow-api-keys.png)

### User Token

1. Go to your Datacoves Launchpad
2. Click Environments on the left-side menu.
3. Click the padlock as pictured above.
4. Note the "Authentication URL" as pictured below.

![Environment Keys Screen](assets/airflow-api-keys.png)

You can use the Authentication URL to request a token such as:

```bash
curl --location '<authentication-url>' \
--header 'Content-Type: application/json' \
--data-raw '{
    "email": "<username>",
    "password": "<password>"
}'
```

You will receive a response similar to:

```bash
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}
```

The `exp` field in the payload will have the token expiration time.

![JWT](assets/api-airflow-jwt-min.png)

Many libraries automate JWT-based authentication and refresh tokens.


## Using a Refresh Token

Once the token expires you can generate a new token or use the `refresh token` to get a new one. Please note that the refresh token also has an expiration time of 30 days.

```bash
curl --location '<refresh-url>' \
--header 'Content-Type: application/json' \
--header 'Cookie: csrftoken=yKEcHY5X7IT4IZOjJLbX4tGLH06I2AKK' \
--data '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}'
```

## Airflow API Documentation

You can consult the Airflow API documentation in your environment with `Swagger UI` or `Redoc`.

![Airflow API docs](assets/api-airflow-doc-min.png)

## Example

### Getting Dags using cURL

```bash
curl --location 'https://<airflow-api-url>/dags' \
--header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGci...'
```

### Getting Dags using the Service Account

First, install dependencies:

```bash
# Optional: make virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip3 install requests
```

And now sample code:

```python
import requests

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGci..."
REFRESH_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGci..."

# Try our request
result = requests.get(
    "https://<airflow-api-url>/dags",
    headers={
        f"Authorization: Bearer {ACCESS_TOKEN}"
    }
)

if result.status_code != 200:
    # Use the refresh token and try again
    result = requests.post(
        "<refresh-url>",
        json={
            "refresh": REFRESH_TOKEN
        }
    )

    if result.status_code != 200:
        # Refresh token is expired
        raise Exception(result.text)

    tokens = result.json()
    ACCESS_TOKEN = tokens['access']
    REFRESH_TOKEN = tokens['refresh']
    
    # Store the new tokens as appropriate and re-try the request
    # If it fails again, abort with error

```

### Getting Dags using a User Account

The code is the same as above, but the following code will fetch a token pair based on user and password:

```
result = requests.post(
    "<authorization-url>",
    json={
        "username": "<user>",
        "password": "<password>",
    }
)
```
