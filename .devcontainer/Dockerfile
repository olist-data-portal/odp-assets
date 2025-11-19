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
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# vscodeユーザーに切り替え
USER vscode
WORKDIR /workspace

# vscodeユーザーでもuvを使えるようにシンボリックリンクを作成
RUN mkdir -p /home/vscode/.local/bin && \
    ln -s /root/.cargo/bin/uv /home/vscode/.local/bin/uv || true
ENV PATH="/home/vscode/.local/bin:${PATH}"

