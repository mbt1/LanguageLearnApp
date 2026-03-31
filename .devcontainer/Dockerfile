FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

ARG PGROLL_VERSION=0.16.1

# ---- Remove stale Yarn repo from base image (broken GPG key) ----
RUN rm -f /etc/apt/sources.list.d/yarn.list

# ---- Add third-party apt repositories ----
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && mkdir -p -m 755 /etc/apt/keyrings \
    && wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg \
       | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
       | tee /etc/apt/sources.list.d/github-cli.list > /dev/null

# ---- Install all apt packages in one layer ----
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        imagemagick \
        librsvg2-bin \
        nodejs \
        postgresql-client \
        gh \
        unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ---- PowerShell (direct install, supports amd64 + arm64) ----
ARG POWERSHELL_VERSION=7.4.6
RUN ARCH=$(dpkg --print-architecture | sed 's/amd64/x64/;s/arm64/arm64/') \
    && curl -fsSL "https://github.com/PowerShell/PowerShell/releases/download/v${POWERSHELL_VERSION}/powershell-${POWERSHELL_VERSION}-linux-${ARCH}.tar.gz" -o /tmp/ps.tar.gz \
    && mkdir -p /opt/microsoft/powershell/7 \
    && tar zxf /tmp/ps.tar.gz -C /opt/microsoft/powershell/7 \
    && chmod +x /opt/microsoft/powershell/7/pwsh \
    && ln -s /opt/microsoft/powershell/7/pwsh /usr/bin/pwsh \
    && rm /tmp/ps.tar.gz

# ---- AWS CLI v2 ----
RUN ARCH=$(uname -m) \
    && curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-${ARCH}.zip" -o /tmp/awscliv2.zip \
    && unzip -q /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install \
    && rm -rf /tmp/awscliv2.zip /tmp/aws

# ---- pnpm ----
RUN npm install -g pnpm

# ---- uv (Python package manager) ----
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# ---- pgroll ----
RUN ARCH=$(dpkg --print-architecture) \
    && wget -qO /usr/local/bin/pgroll \
       "https://github.com/xataio/pgroll/releases/download/v${PGROLL_VERSION}/pgroll.linux.${ARCH}" \
    && chmod +x /usr/local/bin/pgroll

WORKDIR /workspace
