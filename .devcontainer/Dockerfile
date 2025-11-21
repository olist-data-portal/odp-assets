FROM python:3.12-slim

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# デフォルトユーザー（vscode用）を作成し、sudo権限を付与
RUN useradd -m -s /bin/bash vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    mkdir -p /workspace && \
    chown -R vscode:vscode /workspace

# uvのインストール（システム全体で使用可能にするためrootでインストール）
RUN curl -LsSf https://astral.sh/uv/install.sh -o /tmp/uv-install.sh && \
    sh /tmp/uv-install.sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx && \
    chmod +x /usr/local/bin/uv /usr/local/bin/uvx && \
    rm /tmp/uv-install.sh

# vscodeユーザーに切り替え
USER vscode
WORKDIR /workspace

# uvが使えることを確認
ENV PATH="/usr/local/bin:/home/vscode/.local/bin:${PATH}"

