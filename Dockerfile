ARG HELM_VERSION

FROM golang:1.13 as setup
ARG HELM_VERSION
RUN curl -L "https://get.helm.sh/helm-v${HELM_VERSION}-linux-amd64.tar.gz" -o helm.tar.gz \
    && tar -zxvf helm.tar.gz \
    && mv ./linux-amd64/helm /usr/local/bin/helm \
    && helm plugin install https://github.com/chartmuseum/helm-push.git \
    && helm plugin install https://github.com/hypnoglow/helm-s3.git \
    && helm plugin install https://github.com/nouney/helm-gcs.git \
    && helm plugin install https://github.com/jkroepke/helm-secrets --version v3.6.0

ENV GOPATH="/go"

RUN go get -u go.mozilla.org/sops/v3 \
    && cd $GOPATH/src/go.mozilla.org/sops/v3 \
    && make install \
    # remove sops even though go install will overwrite.
    && rm -rf /go/bin/sops \
    && CGO_ENABLED=0 GOOS=linux go install -a -ldflags '-extldflags "-static"' go.mozilla.org/sops/v3/cmd/sops

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

# Install Python3
RUN apk add --no-cache python3 \
    && rm -rf /root/.cache

COPY bin/* /opt/bin/
COPY --from=setup /go/bin/sops /opt/bin

RUN chmod +x /opt/bin/*

ENV PATH="/opt/bin:${PATH}"

RUN apk add --no-cache gnupg \
    && helm plugin install https://github.com/chartmuseum/helm-push.git \
    && helm plugin install https://github.com/hypnoglow/helm-s3.git \
    && helm plugin install https://github.com/nouney/helm-gcs.git \
    && helm plugin install https://github.com/jkroepke/helm-secrets --version v3.6.0

RUN pip install --no-cache-dir awscli==1.16.266

COPY lib/* /opt/lib/

ENV HELM_VERSION ${HELM_VERSION}

ENTRYPOINT ["/opt/bin/release_chart"]
