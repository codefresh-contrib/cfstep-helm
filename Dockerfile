ARG HELM_VERSION
ARG KUBE_VERSION="v1.14.3"
ARG ALPINE_VERSION=3.11
ARG PYTHON_VERSION=3.8

# SETUP
FROM golang:latest as setup
ARG HELM_VERSION
ARG KUBE_VERSION
RUN curl -L "https://storage.googleapis.com/kubernetes-helm/helm-v${HELM_VERSION}-linux-amd64.tar.gz" -o helm.tar.gz \
    && tar -zxvf helm.tar.gz \
    && mv ./linux-amd64/helm /usr/local/bin/helm \
    && helm init --client-only \
    && helm plugin install https://github.com/hypnoglow/helm-s3.git \
    && helm plugin install https://github.com/nouney/helm-gcs.git \
    && helm plugin install https://github.com/chartmuseum/helm-push.git \
    && curl -L https://storage.googleapis.com/kubernetes-release/release/${KUBE_VERSION}/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl \
    && chmod +x /usr/local/bin/kubectl
# Run acceptance tests
COPY Makefile Makefile
COPY bin/ bin/
COPY lib/ lib/
COPY acceptance_tests/ acceptance_tests/
RUN apt-get update \
    && apt-get install -y python3-venv \
    && make acceptance


# MAIN
FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION}

WORKDIR /config

ARG HELM_VERSION
ENV HELM_VERSION ${HELM_VERSION}

RUN echo "HELM_VERSION is set to: ${HELM_VERSION}"

RUN apk add --update ca-certificates && update-ca-certificates \
    && apk add --update --no-cache curl bash jq make git openssl \
    && pip install yq \
    && rm /var/cache/apk/* \
    && rm -rf /tmp/* \
    && rm -rf /root/.cache

COPY --from=setup /usr/local/bin/helm /usr/local/bin/helm
COPY --from=setup /usr/local/bin/kubectl /usr/local/bin/kubectl

RUN bash -c 'if [[ "${HELM_VERSION}" == 2* ]]; then helm init --client-only; else echo "using helm3, no need to initialize helm"; fi'

COPY bin/* /opt/bin/
COPY lib/* /opt/lib/

ENTRYPOINT ["/opt/bin/release_chart"]
