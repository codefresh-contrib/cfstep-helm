ARG HELM_VERSION
FROM golang:latest as setup
ARG HELM_VERSION
RUN curl -L "https://storage.googleapis.com/kubernetes-helm/helm-v${HELM_VERSION}-linux-amd64.tar.gz" -o helm.tar.gz \
    && tar -zxvf helm.tar.gz \
    && mv ./linux-amd64/helm /usr/local/bin/helm \
    && helm init --client-only \
    && helm plugin install https://github.com/hypnoglow/helm-s3.git \
    && helm plugin install https://github.com/nouney/helm-gcs.git 

FROM codefresh/kube-helm:${HELM_VERSION}
COPY --from=setup /root/.helm/ /root/.helm/
COPY bin/* /opt/bin/
RUN chmod +x /opt/bin/*

ENTRYPOINT ["/opt/bin/release_chart"]
