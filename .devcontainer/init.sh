#!/bin/bash
set -e

echo "=== DevContainer初期化スクリプト ==="

# .envファイルから環境変数を読み込む
ENV_FILE="/workspace/odp-assets/.env"
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment variables from .env file..."
    # .envファイルからコメント行と空行を除外して読み込む
    # set -aで自動的にexportする
    set -a
    # grepでコメント行と空行を除外し、sourceで読み込む
    source <(grep -v '^#' "$ENV_FILE" | grep -v '^$')
    set +a
    echo "Environment variables loaded from .env"
else
    echo "Warning: .env file not found at $ENV_FILE"
fi

# GCP認証の設定
# gcloud auth application-default loginを使用（対話的認証）
echo "GCP認証を設定します..."

if command -v gcloud &> /dev/null; then
    # 既にApplication Default Credentialsが設定されているか確認
    if gcloud auth application-default print-access-token &>/dev/null; then
        echo "✓ Application Default Credentialsが既に設定されています"
    else
        echo ""
        echo "gcloud auth application-default loginを実行します..."
        echo "表示されたURLにアクセスして認証コードを入力してください。"
        echo ""
        
        # --no-launch-browserオプションを使用（Dockerコンテナ内ではブラウザが開かないため）
        # エラーが発生しても続行する（set -eの影響を受けないように）
        set +e
        gcloud auth application-default login --no-launch-browser 2>&1
        EXIT_CODE=$?
        set -e
        
        if [ $EXIT_CODE -eq 0 ]; then
            echo ""
            echo "✓ gcloud auth application-default loginが完了しました"
            echo "✓ Application Default Credentialsが設定されました"
        else
            echo ""
            echo "⚠ Warning: gcloud auth application-default loginに失敗しました（または中断されました）"
            echo "手動で以下のコマンドを実行してください："
            echo "  gcloud auth application-default login --no-launch-browser"
        fi
    fi
else
    echo "⚠ Warning: gcloud CLIがインストールされていません"
    echo "gcloud CLIをインストールしてから、以下のコマンドを実行してください："
    echo "  gcloud auth application-default login --no-launch-browser"
fi

echo "=== 初期化完了 ==="

