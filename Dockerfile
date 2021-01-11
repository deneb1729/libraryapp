FROM python:3.7-alpine

LABEL manteiner="deneb1729" \
      manteiner_mail="joelquispeunju@gmail.com"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /usr/src/app

WORKDIR $APP_HOME

COPY requirements.txt $APP_HOME

RUN apk update \
    && apk add --no-cache --virtual .build-deps \
    jpeg-dev \
    zlib-dev \
    gcc \
    libffi-dev \
    musl-dev \
    postgresql-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install gunicorn \
    && find /usr/local \
        \( -type d -a -name test -o -name tests \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' + \
    && runDeps="$( \
        scanelf --needed --nobanner --recursive /usr/local \
                | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
                | sort -u \
                | xargs -r apk info --installed \
                | sort -u \
    )" \
    && apk add --virtual .rundeps $runDeps \
    && apk del .build-deps

COPY . $APP_HOME/
RUN addgroup -S john && adduser -S john -G john \
    && chown -R john:john $APP_HOME
USER john

ENTRYPOINT [ "gunicorn","ducasa.wsgi:application","--bind","0.0.0.0:8000","--log-level","info" ]
