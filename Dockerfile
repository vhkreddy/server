FROM python:3
ARG BUILD_DATE
ARG VCS_REF


ADD . /code/
WORKDIR /code
RUN pip install -r requirements.txt

