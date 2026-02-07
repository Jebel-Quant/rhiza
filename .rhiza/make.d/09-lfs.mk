## lfs.mk - Git LFS (Large File Storage) setup
# This file is included by the main Makefile

# Declare phony targets
.PHONY: lfs-install lfs-pull lfs-track lfs-status

##@ Git LFS
lfs-install: ## install git-lfs and configure it for this repository
	@# -----------------------------
	@# Git LFS install (cross-platform)
	@# -----------------------------
	@UNAME_S=$$(uname -s); \
	UNAME_M=$$(uname -m); \
	if [ "$$UNAME_S" = "Darwin" ]; then \
		printf "${BLUE}[INFO] macOS detected ($$UNAME_M)${RESET}\n"; \
		mkdir -p .local/bin .local/tmp; \
		GIT_LFS_VERSION=$$(curl -sI https://github.com/git-lfs/git-lfs/releases/latest | grep -i '^location:' | sed 's/.*tag\/v//;s/[[:space:]]*$$//'); \
		printf "${BLUE}[INFO] Installing git-lfs v$$GIT_LFS_VERSION${RESET}\n"; \
		if [ "$$UNAME_M" = "arm64" ]; then \
			curl -fL -o .local/tmp/git-lfs.zip \
				"https://github.com/git-lfs/git-lfs/releases/download/v$$GIT_LFS_VERSION/git-lfs-darwin-arm64-v$$GIT_LFS_VERSION.zip"; \
		else \
			curl -fL -o .local/tmp/git-lfs.zip \
				"https://github.com/git-lfs/git-lfs/releases/download/v$$GIT_LFS_VERSION/git-lfs-darwin-amd64-v$$GIT_LFS_VERSION.zip"; \
		fi; \
		unzip -o -q .local/tmp/git-lfs.zip -d .local/tmp; \
		cp .local/tmp/git-lfs-*/git-lfs .local/bin/; \
		chmod +x .local/bin/git-lfs; \
		PATH=$$PWD/.local/bin:$$PATH git-lfs install; \
		rm -rf .local/tmp; \
	elif [ "$$UNAME_S" = "Linux" ]; then \
		printf "${BLUE}[INFO] Linux detected${RESET}\n"; \
		if ! command -v git-lfs >/dev/null 2>&1; then \
			printf "${BLUE}[INFO] Installing git-lfs via apt...${RESET}\n"; \
			apt-get update && apt-get install -y git-lfs; \
		fi; \
		git lfs install; \
	else \
		printf "${RED}[ERROR] Unsupported OS: $$UNAME_S${RESET}\n"; \
		exit 1; \
	fi

lfs-pull: ## download all git-lfs files for the current branch
	@printf "${BLUE}[INFO] Pulling Git LFS files...${RESET}\n"
	@git lfs pull

lfs-track: ## list all file patterns tracked by git-lfs
	@printf "${BLUE}[INFO] Git LFS tracked patterns:${RESET}\n"
	@git lfs track

lfs-status: ## show git-lfs file status
	@printf "${BLUE}[INFO] Git LFS status:${RESET}\n"
	@git lfs status
