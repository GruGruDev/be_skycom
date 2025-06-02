# Pull official base image
FROM python:3.10.11-slim-buster

# Create the app user
RUN addgroup --system app && adduser --system --group app

WORKDIR /app/

# https://docs.python.org/3/using/cmdline.html#envvar-PYTHONDONTWRITEBYTECODE
# Prevents Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE 1

# ensures that the python output is sent straight to terminal (e.g. your container log)
# without being first buffered and that you can see the output of your application (e.g. django logs)
# in real time. Equivalent to python -u: https://docs.python.org/3/using/cmdline.html#cmdoption-u
ENV PYTHONUNBUFFERED 1
ENV ENVIRONMENT prod

# Install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc libpq-dev \
  && apt-get clean

# Install python dependencies
RUN pip install --upgrade pip
RUN pip install -U setuptools==70.1.1
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Add src code
COPY ./src .

# Add start script
COPY ./k8s/tam-prod/scripts/pre_start_app.sh .
RUN chmod +x pre_start_app.sh

# Add start script
COPY ./k8s/tam-prod/scripts/start_app.sh .
RUN chmod +x start_app.sh


ENV PYTHONPATH=/app

RUN mkdir /app/staticfiles
RUN mkdir /app/mediafiles

# Chown all the files to the app user
RUN chown -R app:app /app

# Change to the app user
USER app

EXPOSE 8000
CMD ["/app/start_app.sh"]
