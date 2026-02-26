FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

ARG PGROLL_VERSION=0.16.1

# ---- Remove stale Yarn repo from base image (broken GPG key) ----
RUN rm -f /etc/apt/sources.list.d/yarn.list

# ---- Add third-party apt repositories ----
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && wget -q "https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb" \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && mkdir -p -m 755 /etc/apt/keyrings \
    && wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg \
       | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
       | tee /etc/apt/sources.list.d/github-cli.list > /dev/null

# ---- Install all apt packages in one layer ----
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        nodejs \
        postgresql-client \
        powershell \
        gh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ---- pnpm ----
RUN npm install -g pnpm

# ---- uv (Python package manager) ----
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# ---- pgroll ----
RUN ARCH=$(dpkg --print-architecture) \
    && wget -qO /usr/local/bin/pgroll \
       "https://github.com/xataio/pgroll/releases/download/v${PGROLL_VERSION}/pgroll.linux.${ARCH}" \
    && chmod +x /usr/local/bin/pgroll
