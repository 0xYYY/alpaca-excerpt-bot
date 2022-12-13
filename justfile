deploy:
    bash scripts/deploy.sh
trigger:
    gcloud pubsub topics publish noon --attribute=alpaca=true
