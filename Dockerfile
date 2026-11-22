FROM python:3.14.10-slim-trixie

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONUNBUFFERED=1
ENV WORKDIR=/opt/project/server
ENV PYTHONPATH=/opt/project/server/src

RUN mkdir -p ${WORKDIR}
WORKDIR ${WORKDIR}

RUN apt-get update && \
    apt-get install --no-install-recommends -y curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ${WORKDIR}/
RUN pip install --no-cache-dir -r ${WORKDIR}/requirements.txt
COPY . ${WORKDIR}

CMD ["uvicorn", "fastapi_base.main:create_app", "--factory", "--reload", "--host", "0.0.0.0"]
