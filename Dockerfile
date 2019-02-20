ARG HELM_VERSION

FROM golang:latest as setup
ARG HELM_VERSION
RUN curl -L "https://storage.googleapis.com/kubernetes-helm/helm-v${HELM_VERSION}-linux-amd64.tar.gz" -o helm.tar.gz \
    && tar -zxvf helm.tar.gz \
    && mv ./linux-amd64/helm /usr/local/bin/helm \
    && helm init --client-only \
    && helm plugin install https://github.com/hypnoglow/helm-s3.git \
    && helm plugin install https://github.com/nouney/helm-gcs.git \
    && helm plugin install https://github.com/chartmuseum/helm-push.git \
    && go get go.mozilla.org/sops/cmd/sops \
    && CGO_ENABLED=0 GOOS=linux go install -a -ldflags '-extldflags "-static"' go.mozilla.org/sops/cmd/sops \
    && helm plugin install https://github.com/futuresimple/helm-secrets

# Run acceptance tests
COPY Makefile Makefile
COPY bin/ bin/
COPY lib/ lib/
COPY acceptance_tests/ acceptance_tests/
RUN apt-get update \
    && apt-get install -y python3-venv \
    && make acceptance

FROM codefresh/kube-helm:${HELM_VERSION}
ARG HELM_VERSION
COPY --from=setup /root/.helm/ /root/.helm/
COPY bin/* /opt/bin/
RUN chmod +x /opt/bin/*

COPY --from=setup /go/bin/sops /go/bin/sops
RUN apk add --no-cache gnupg \
    && chmod +x /go/bin/sops
ENV PATH="/go/bin:${PATH}"
COPY lib/* /opt/lib/

# Install Python3
RUN apk add --no-cache python3 \
    && rm -rf /root/.cache

ENV HELM_VERSION ${HELM_VERSION}

ENTRYPOINT ["/opt/bin/release_chart"]
