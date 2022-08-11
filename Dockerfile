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
    && apt-get purge --assume-yes \
        python3-dask \
        python3-numpy \
    && apt-get autoremove --assume-yes \
    && cp --verbose src/create_config.py ${HOME}/ \
    && pip install --upgrade pip  \
    && pip install \
            --no-cache-dir \
            --quiet \
            --disable-pip-version-check \
            --no-warn-script-location \
            --requirement requirements.txt \
    && pip install . \
    && mkdir -pv ${HOME}/data \
    && apt-get autoremove --assume-yes \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -pv ${HOME}/odc/DATA

COPY ./src ${HOME}

RUN sed --in-place 's@echo "Trying to generate openapi.yml"@echo "Generating ODC based config"\npython3 /pygeoapi/create_config.py --infile=/pygeoapi/local.config.init.yml --outfile=/pygeoapi/local.config.yml --exclude-products=${EXCLUDE_PRODUCTS}\n\necho "Trying to generate openapi.yml"@g' /entrypoint.sh

COPY default.config.yml /pygeoapi/local.config.init.yml
COPY default.datacube.conf /pygeoapi/datacube.conf

ARG GIT_COMMIT
LABEL org.opencontainers.image.revision="${GIT_COMMIT}"

ARG BUILD_DATE
LABEL org.opencontainers.image.created="${BUILD_DATE}"

ARG VERSION=latest
ARG IMG_REF=52north/ogc-tb-17-pygeoapi
LABEL org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.ref.name="${IMG_REF}_${VERSION}"
