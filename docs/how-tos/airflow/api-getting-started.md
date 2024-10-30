# Airflow API - Getting Started

## Requirements

1. Airflow API enabled.
2. Valid credentials: `username` and `password`.
3. Environment slug.
3. **Authentication URL**: https://api.<domain\>
4. **Airflow API URL**: https://api-airflow-<environment-slug\>.<domain\>/api/v1 E.g: `https://api-airflow-dev123.datacoves.com`

## Authentication

### Request

```bash
curl --location 'https://<authentication-url>/api/token/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "email": "<username>",
    "password": "<password>"
}'
```

### Response

```bash
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}
```

The `exp` field in the payload will have the token expiration time.

![JWT](assets/api-airflow-jwt-min.png)

## Refresh token

Once the token expires you can generate a new token or use the `refresh token` to get a new one. Please note that the refresh token also has an expiration time.

```bash
curl --location 'https://<authentication-url>/api/token/refresh/' \
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

Getting Dags

```bash
curl --location 'https://<airflow-api-url>.datacoveslocal.com/api/v1/dags' \
--header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGci...'
```
