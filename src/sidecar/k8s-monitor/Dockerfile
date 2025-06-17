FROM python:3.12-slim

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY ./app /app
RUN ln -s /app/app.py /usr/local/bin/datacoves
COPY ./requirements.txt /tmp/requirements.txt

# set work directory
WORKDIR /app

RUN apt-get clean \
    apt-get update -y && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    adduser --disabled-password --no-create-home app-user && \
    chown -R app-user:app-user /app && \
    chmod -R 755 /app

USER app-user

ENV PATH="/py/bin:$PATH"
CMD ["datacoves", "--help"]
