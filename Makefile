VERSION ?= v0.7.0
REMOTE ?= origin
DOCKER_REPO ?= jvstein/bitcoin-prometheus-exporter
PLATFORMS ?= linux/386,linux/amd64,linux/arm/v6,linux/arm/v7,linux/arm64,linux/ppc64le,linux/s390x
LATEST ?= latest

# Builds for local platform only.
docker:
	docker buildx build \
		--pull \
		--load \
		-t $(DOCKER_REPO):$(LATEST) \
		-t $(DOCKER_REPO):$(VERSION) \
	  $(PWD)

# Builds and pushes for all platforms.
docker-release:
	docker buildx build \
		--pull \
		--push \
		--platform $(PLATFORMS) \
		-t $(DOCKER_REPO):$(LATEST) \
		-t $(DOCKER_REPO):$(VERSION) \
	  $(PWD)

git-tag:
	git tag -s $(VERSION) -m "Release $(VERSION)"

git-tag-push:
	git push --tags $(REMOTE)
	git push $(REMOTE) master
