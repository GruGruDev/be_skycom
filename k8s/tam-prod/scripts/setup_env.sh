#!/bin/sh

rm -rf /src/.env

echo DEBUG=0 >>./src/.env
echo SECRET_KEY=$SECRET_KEY_DEV >>./src/.env # to_fix
echo DJANGO_ALLOWED_HOSTS=$DJANGO_ALLOWED_HOSTS_TAM >>./src/.env
echo DJANGO_ALLOWED_CIDR_NETS=$DJANGO_ALLOWED_CIDR_NETS_TAM >>./src/.env
echo DJANGO_CORS_ALLOWED_ORIGINS=$DJANGO_CORS_ALLOWED_ORIGINS_TAM >>./src/.env

# Database
echo SQL_ENGINE=$SQL_ENGINE >> ./src/.env
echo SQL_DATABASE=$SQL_DATABASE_PROD_TAM >> ./src/.env
echo SQL_USER=$SQL_USER_PROD_TAM >> ./src/.env
echo SQL_PASSWORD=$SQL_PASSWORD_PROD_TAM >> ./src/.env
echo SQL_HOST=$SQL_HOST_PROD_TAM >> ./src/.env
echo SQL_PORT=$SQL_PORT_PROD_TAM >> ./src/.env

# Config
echo UVICORN_NUMBER_THREADS=$UVICORN_NUMBER_THREADS_KMV >> ./src/.env # to_fix
echo UVICORN_NUMBER_WORKER=$UVICORN_NUMBER_WORKER_KMV >> ./src/.env # to_fix

# Storages
echo AWS_S3_ENDPOINT_URL=$AWS_S3_ENDPOINT_URL >> ./src/.env
echo AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID >> ./src/.env
echo AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY >> ./src/.env
echo AWS_STORAGE_BUCKET_NAME=$AWS_STORAGE_BUCKET_NAME >> ./src/.env # to_fix
echo AWS_S3_REGION_NAME=$AWS_S3_REGION_NAME>> ./src/.env # to_fix

# Info commit
echo CI_REGISTRY=$CI_REGISTRY  >> ./src/.env
echo CI_COMMIT_TIMESTAMP=$CI_COMMIT_TIMESTAMP >> ./src/.env
echo CI_COMMIT_SHA=$CI_COMMIT_SHA  >> ./src/.env

# Airflow
echo URL_ROOT=$URL_ROOT_TAM_PROD >> ./src/.env

# sentry
echo SENTRY_DSN=$SENTRY_DSN >> ./src/.env
