# Copyright (C) 2021-2022 52°North Spatial Information Research GmbH
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# If the program is linked with libraries which are licensed under one of
# the following licenses, the combination of the program with the linked
# library is not considered a "derivative work" of the program:
#
#     - Apache License, version 2.0
#     - Apache Software License, version 1.0
#     - GNU Lesser General Public License, version 3
#     - Mozilla Public License, versions 1.0, 1.1 and 2.0
#     - Common Development and Distribution License (CDDL), version 1.0
#
# Therefore the distribution of the program linked with libraries licensed
# under the aforementioned licenses, is permitted by the copyright holders
# if the distribution is compliant with both the GNU General Public
# License version 2 and the aforementioned licenses.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# build with
#
#      --build-arg GIT_COMMIT=$(git rev-parse -q --verify HEAD)
#      --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
#
# See https://wiki.52north.org/Documentation/ImageAndContainerLabelSpecification
# regarding the used labels
#
# Information on the geopython/pygeoapi Docker image
# - https://docs.pygeoapi.io/en/latest/running-with-docker.html
# - https://github.com/geopython/pygeoapi/blob/master/Dockerfile
#
FROM geopython/pygeoapi:latest

ENV PYTHONUNBUFFERED=1
ENV EXCLUDE_PRODUCTS=""
ARG HOME=/pygeoapi

LABEL maintainer="Jürrens, Eike Hinderk <e.h.juerrens@52north.org>" \
      org.opencontainers.image.authors="Jürrens, Eike Hinderk <e.h.juerrens@52north.org>; Pontius, Martin <m.pontius@52north.org>" \
      org.opencontainers.image.url="https://github.com/52North/pygeoapi-odc-provider.git" \
      org.opencontainers.image.vendor="52°North GmbH" \
      org.opencontainers.image.licenses="GPL-3.0-or-later" \
      org.opencontainers.image.title="52°North GeoDataCube Server" \
      org.opencontainers.image.description="PyGeoAPI based webinterface for OpenDataCube"

WORKDIR ${HOME}

RUN apt-get update \
    && apt-get install --assume-yes \
        libpq-dev \
        libglib2.0-0 \
    && apt-get autoremove --assume-yes \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt ./setup.py /tmp/

COPY ./src /tmp/src

RUN cd /tmp/ \
    && pip install --upgrade pip  \
    && pip install \
            --no-cache-dir \
            --quiet \
            --disable-pip-version-check \
            --no-warn-script-location \
            --requirement requirements.txt \
    && pip install . \
    && cp -v /tmp/src/create_config.py ${HOME}

COPY default.config.yml ${HOME}/local.config.init.yml
COPY default.datacube.conf ${HOME}/datacube.conf

RUN sed --in-place 's@echo "Trying to generate openapi.yml"@echo "Generating ODC based config"\npython3 ${PYGEOAPI_HOME}/create_config.py --infile=${PYGEOAPI_HOME}/local.config.init.yml --outfile=${PYGEOAPI_HOME}/local.config.yml --exclude-products=${EXCLUDE_PRODUCTS}\n\necho "Trying to generate openapi.yml"@g' /entrypoint.sh

ARG GIT_COMMIT
LABEL org.opencontainers.image.revision="${GIT_COMMIT}"

ARG BUILD_DATE
LABEL org.opencontainers.image.created="${BUILD_DATE}"

ARG VERSION=latest
ARG IMG_REF=52north/pygeoapi-opendatacube
LABEL org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.ref.name="${IMG_REF}_${VERSION}"
