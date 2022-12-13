#!/usr/bin/env bash

PROJECT_ID=$(gcloud config list --format 'value(core.project)')

function join_array {
    local arr=("$@")
    local result="$(
        IFS=,
        echo "${arr[*]}"
    )"
    echo "$result"
}

SECRETS=(
    "API_ID=ALPACA_TELEGRAM_API_ID:latest"
    "API_HASH=ALPACA_TELEGRAM_API_HASH:latest"
    "USER_SESSION_KEY=ALPACA_TELEGRAM_USER_SESSION_KEY:latest"
    "BOT_SESSION_KEY=ALPACA_TELEGRAM_BOT_SESSION_KEY:latest"
)

gcloud functions deploy alpaca-excerpt-bot --region=us-central1 --memory=128Mi --runtime python310 \
    --allow-unauthenticated --entry-point=main --trigger-topic=noon \
    --set-secrets="$(join_array "${SECRETS[@]}")" --gen2
