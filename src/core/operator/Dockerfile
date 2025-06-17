# Build the manager binary
FROM golang:1.17 as builder

RUN curl -LO https://get.helm.sh/helm-v3.11.0-linux-amd64.tar.gz && \
    tar -xzf helm-v3.11.0-linux-amd64.tar.gz && \
    mv linux-amd64/helm /usr/bin/helm

WORKDIR /workspace
# Copy the Go Modules manifests
COPY go.mod go.mod
COPY go.sum go.sum
# cache deps before building and copying source so that we don't need to re-download as much
# and so that source changes don't invalidate our downloaded layer
RUN go mod download

# Copy the go source
COPY main.go main.go
COPY api/ api/
COPY helm/ helm/
COPY controllers/ controllers/

# Build
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -a -o manager main.go

# Copy and build fake helm binary
COPY cmd/ cmd/
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -a -o fake_helm cmd/fake_helm/fake_helm.go

# Use distroless as minimal base image to package the manager binary
# Refer to https://github.com/GoogleContainerTools/distroless for more details
FROM gcr.io/distroless/static:nonroot
LABEL com.datacoves.from=gcr.io/distroless/static:nonroot
LABEL com.datacoves.version.core-operator='0.3.0'
LABEL com.datacoves.library.core-operator.golang='1.17'
LABEL com.datacoves.library.core-operator.helm='3.11'

WORKDIR /
COPY --from=builder /workspace/manager .
COPY --from=builder /usr/bin/helm /usr/bin/helm
# COPY --from=builder /workspace/fake_helm /usr/bin/helm
USER 65532:65532

ENTRYPOINT ["/manager"]
