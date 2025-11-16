# ==================================
# Stage: 共通 APT ベース（builder 用）
# ==================================
FROM ubuntu:noble AS aptbase
ENV DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl tar unzip gnupg lsb-release python3 && \
    rm -rf /var/lib/apt/lists/*

# =============================
# Stage: GitHub CLI (gh) fetch
# =============================
FROM aptbase AS ghfetch
ARG GH_VERSION=2.53.0
RUN set -eux; \
    arch="$(uname -m)"; \
    case "${arch}" in \
    x86_64) GH_ARCH=amd64 ;; \
    aarch64|arm64) GH_ARCH=arm64 ;; \
    *) echo "Unsupported arch: ${arch}"; exit 1 ;; \
    esac; \
    curl -fsSL -o /tmp/gh.tgz \
    "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_${GH_ARCH}.tar.gz" && \
    tar -C /tmp -xzf /tmp/gh.tgz && \
    install -m 0755 "/tmp/gh_${GH_VERSION}_linux_${GH_ARCH}/bin/gh" /gh && \
    rm -rf /tmp/gh.tgz "/tmp/gh_${GH_VERSION}_linux_${GH_ARCH}"

# ===========================
# Stage: AWS CLI v2 builder
# ===========================
FROM aptbase AS awsclifetch
RUN curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m).zip" -o /tmp/awscliv2.zip && \
    unzip -q /tmp/awscliv2.zip -d /tmp && \
    /tmp/aws/install && \
    rm -rf /tmp/aws /tmp/awscliv2.zip

# ===========================
# Stage: gcloud SDK builder
# ===========================
FROM aptbase AS gcloudfetch
RUN set -eux; \
    arch="$(uname -m)"; \
    case "${arch}" in \
    x86_64) gcloud_arch="x86_64" ;; \
    aarch64) gcloud_arch="arm" ;; \
    *) echo "Unsupported architecture: ${arch}" && exit 1 ;; \
    esac; \
    curl -fsSL "https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-${gcloud_arch}.tar.gz" \
    | tar -xzf - -C /opt && \
    /opt/google-cloud-sdk/install.sh --quiet --path-update=false --usage-reporting=false && \
    /opt/google-cloud-sdk/bin/gcloud components list && \
    /opt/google-cloud-sdk/bin/gcloud components remove --quiet \
    alpha beta anthoscli \
    app-engine-java app-engine-python app-engine-python-extras app-engine-go \
    cloud-datastore-emulator pubsub-emulator \
    kubectl kustomize skaffold minikube \
    docker-credential-gcr cloud-run-proxy 2>&1 || true && \
    rm -rf /opt/google-cloud-sdk/help \
    /opt/google-cloud-sdk/.install/.backup \
    /opt/google-cloud-sdk/.git*

# =======================================
# Stage: Amazon Q Developer CLI fetch
# =======================================
FROM aptbase AS qfetch
RUN set -eux; \
    arch="$(uname -m)"; \
    case "${arch}" in \
    x86_64) Q_ARCH=x86_64 ;; \
    aarch64|arm64) Q_ARCH=aarch64 ;; \
    *) echo "Unsupported arch: ${arch}"; exit 1 ;; \
    esac; \
    curl -fsSL -o /tmp/q.zip \
    "https://desktop-release.q.us-east-1.amazonaws.com/latest/q-${Q_ARCH}-linux.zip" && \
    unzip -q /tmp/q.zip -d /tmp && \
    mkdir -p /opt/amazon-q && \
    cp -r /tmp/q/* /opt/amazon-q/ && \
    chmod +x /opt/amazon-q/bin/q && \
    rm -rf /tmp/q.zip /tmp/q

# =======================================
# Stage: Node builder
# =======================================
FROM node:20-bullseye-slim AS nodebuilder
RUN npm config set prefix /opt/node-globals && \
    npm i -g \
    @playwright/test \
    @anthropic-ai/claude-code \
    aws-cdk aws-cdk-lib typescript \
    @google/gemini-cli \
    @openai/codex && \
    rm -rf /root/.npm /root/.cache

# ================
# Stage: Final
# ================
FROM ubuntu:noble

ENV DEBIAN_FRONTEND=noninteractive

# ---- APT は 1 レイヤに集約。
RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
    locales git wget vim sudo nano jq make \
    curl ca-certificates gnupg lsb-release \
    libnss3 libxrandr2 libxss1; \
    install -m 0755 -d /etc/apt/keyrings; \
    # Docker リポジトリ
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg; \
    chmod a+r /etc/apt/keyrings/docker.gpg; \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    > /etc/apt/sources.list.d/docker.list; \
    # HashiCorp（Terraform）
    curl -fsSL https://apt.releases.hashicorp.com/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/hashicorp-archive-keyring.gpg; \
    echo "deb [signed-by=/etc/apt/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
    > /etc/apt/sources.list.d/hashicorp.list; \
    # リポジトリ追加後に再度update
    apt-get update; \
    apt-get install -y --no-install-recommends \
    docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin \
    terraform; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

# ロケール
RUN locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

# uv/uvx（単一バイナリのみ）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# gh（単一バイナリのみ）
COPY --from=ghfetch /gh /usr/local/bin/gh
RUN gh --version

# awscli（公式パスごとコピー → 正しい symlink で動作）
COPY --from=awsclifetch /usr/local/aws-cli /usr/local/aws-cli
RUN ln -s /usr/local/aws-cli/v2/current/bin/aws /usr/local/bin/aws

# gcloud（削減済みツリー）
COPY --from=gcloudfetch /opt/google-cloud-sdk /opt/google-cloud-sdk
RUN ln -s /opt/google-cloud-sdk/bin/gcloud /usr/local/bin/gcloud && \
    ln -s /opt/google-cloud-sdk/bin/gsutil /usr/local/bin/gsutil && \
    ln -s /opt/google-cloud-sdk/bin/bq /usr/local/bin/bq

# Amazon Q Developer CLI（zipから抽出）
COPY --from=qfetch /opt/amazon-q /opt/amazon-q
RUN ln -s /opt/amazon-q/bin/q /usr/local/bin/q && \
    ln -s /opt/amazon-q/bin/qchat /usr/local/bin/qchat && \
    ln -s /opt/amazon-q/bin/qterm /usr/local/bin/qterm

# Node.js 本体（/usr/local 配下の Node.js ランタイム）
COPY --from=nodebuilder /usr/local/bin/node /usr/local/bin/node
COPY --from=nodebuilder /usr/local/lib/node_modules /usr/local/lib/node_modules
# npm/npxはシンボリックリンクなので、node_modulesコピー後に再作成
RUN ln -s /usr/local/bin/node /usr/local/bin/nodejs && \
    ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

# Node グローバル CLI（Playwright CLI を含む）
COPY --from=nodebuilder /opt/node-globals /opt/node-globals
ENV PATH="/opt/node-globals/bin:${PATH}"

COPY --from=mcpjungle/mcpjungle:latest /mcpjungle /usr/local/bin/mcpjungle

# 確認（任意）
RUN node --version && npm --version && playwright --version

# ユーザー設定
ARG USERNAME="ubuntu"
RUN usermod -aG users $USERNAME && \
    echo '%users ALL=(ALL:ALL) NOPASSWD: ALL' > /etc/sudoers.d/users && \
    echo "$USERNAME ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/users /etc/sudoers.d/$USERNAME

# Create mount point structure for config files (as root)
RUN mkdir -p /mnt/claude /mnt/clasp /mnt/git && \
    touch /mnt/claude/config.json /mnt/clasp/config.json /mnt/git/config /mnt/git/credentials && \
    chown -R $USERNAME:$USERNAME /mnt

USER ${USERNAME}
WORKDIR /home/${USERNAME}/work

# Initialize Amazon Q CLI
RUN q setup --no-confirm

RUN playwright install --with-deps chromium

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN git config --global credential.helper store

VOLUME  /home/${USERNAME}

ENTRYPOINT [ "entrypoint.sh" ]
