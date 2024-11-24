FROM python:3.12.7-alpine3.20

ENV PYTHONUNBUFFERED 1

COPY . /ist

WORKDIR /ist
EXPOSE 8000
ENV DEBUG=1

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client && \
    apk add --update --no-cache --virtual .tmp-deps \
        build-base postgresql-dev musl-dev linux-headers && \
    /py/bin/pip install -e '.[dev]' && \
    apk del .tmp-deps && \
    adduser --disabled-password --no-create-home istuser && \
    mkdir -p /vol/web/static && \
    chown -R istuser:istuser /vol && \
    chmod -R 755 /vol && \
    chmod -R 755 . && \
    chmod -R +x ./scripts

ENV PATH="/ist/scripts:/py/bin:$PATH"

USER istuser

CMD ["run.sh"]
