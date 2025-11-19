#!/bin/bash
set -e

# Select workspace.yaml based on environment
# If GCP_PROJECT_ID is set, use production workspace.yaml
# Otherwise, use local workspace.yaml
if [ -n "$GCP_PROJECT_ID" ]; then
    echo "Using production workspace.yaml (GCP environment)"
    cp $DAGSTER_HOME/workspace.yaml.production $DAGSTER_HOME/workspace.yaml
    
    # Replace placeholder with actual service name if provided
    if [ -n "$DAGSTER_USER_CODE_SERVICE" ]; then
        echo "Replacing DAGSTER_USER_CODE_SERVICE_PLACEHOLDER with $DAGSTER_USER_CODE_SERVICE"
        sed -i "s/DAGSTER_USER_CODE_SERVICE_PLACEHOLDER/$DAGSTER_USER_CODE_SERVICE/g" $DAGSTER_HOME/workspace.yaml
    else
        echo "Warning: DAGSTER_USER_CODE_SERVICE is not set, using placeholder"
    fi
else
    echo "Using local workspace.yaml (local development)"
    cp $DAGSTER_HOME/workspace.yaml.local $DAGSTER_HOME/workspace.yaml
fi

# Execute the original command
exec "$@"

