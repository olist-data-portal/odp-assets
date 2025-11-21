#!/bin/bash
set -e

export DAGSTER_HOME="${DAGSTER_HOME:-/opt/dagster/dagster_home/}"

# workspace.yamlの環境変数置き換え
if [ -n "$DAGSTER_USER_CODE_SERVICE" ]; then
    HOST_ONLY=$(echo "$DAGSTER_USER_CODE_SERVICE" | sed 's/:.*$//')
    PORT_ONLY=$(echo "$DAGSTER_USER_CODE_SERVICE" | sed 's/^.*://')
    
    echo "Replacing DAGSTER_USER_CODE_SERVICE_PLACEHOLDER with $HOST_ONLY in workspace.yaml"
    sed -i "s|DAGSTER_USER_CODE_SERVICE_PLACEHOLDER|$HOST_ONLY|g" $DAGSTER_HOME/workspace.yaml
    
    # ポート番号も環境変数から取得できる場合は置き換え
    if [ -n "$DAGSTER_USER_CODE_SERVICE_PORT" ]; then
        echo "Replacing port in workspace.yaml with $DAGSTER_USER_CODE_SERVICE_PORT"
        sed -i "s|port: 443|port: $DAGSTER_USER_CODE_SERVICE_PORT|g" $DAGSTER_HOME/workspace.yaml
    elif [ -n "$PORT_ONLY" ]; then
        echo "Replacing port in workspace.yaml with $PORT_ONLY"
        sed -i "s|port: 443|port: $PORT_ONLY|g" $DAGSTER_HOME/workspace.yaml
    fi
    
    # 置き換えが成功したか確認
    if grep -q "DAGSTER_USER_CODE_SERVICE_PLACEHOLDER" $DAGSTER_HOME/workspace.yaml; then
        echo "WARNING: DAGSTER_USER_CODE_SERVICE_PLACEHOLDER still found in workspace.yaml after replacement"
    else
        echo "Successfully replaced DAGSTER_USER_CODE_SERVICE_PLACEHOLDER in workspace.yaml"
    fi
else
    echo "WARNING: DAGSTER_USER_CODE_SERVICE environment variable is not set"
    echo "workspace.yaml may contain DAGSTER_USER_CODE_SERVICE_PLACEHOLDER"
fi

# workspace.yamlの内容を確認（デバッグ用）
if [ "${DEBUG:-0}" = "1" ]; then
    echo "=== workspace.yaml content ==="
    cat $DAGSTER_HOME/workspace.yaml
    echo "=============================="
fi

exec "$@"

