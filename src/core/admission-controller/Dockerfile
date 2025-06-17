FROM python:3.11-alpine
LABEL com.datacoves.from=python:3.11-alpine
LABEL com.datacoves.library.admission-controller.fastapi=0.86.0
WORKDIR /src

COPY requirements.txt /src/

RUN pip install -r /src/requirements.txt

COPY api.py entrypoint.sh /src/

ENTRYPOINT ["/src/entrypoint.sh"]
