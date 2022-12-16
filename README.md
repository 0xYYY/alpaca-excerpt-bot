# 🦙 Alpaca Excerpt Bot 🤖

Extract news under topics of interest (MEV, security, development) from [DefiLlama Round Up](https://defillama.com/roundup) and forward to [DefiLlama Round Up for Devs](https://t.me/defillama_roundup_dev).

## Requirements

### Python Packages

-   [`functions_framework`](https://github.com/GoogleCloudPlatform/functions-framework-python): Google
    Cloud Functions framework.
-   [`telethon`](https://github.com/LonamiWebs/Telethon): Telegram library for MTProto and Bot API.
-   [`ipdb`](https://github.com/gotcha/ipdb): debugging tool.

### Tools

-   [`black`](https://github.com/psf/black): code formatting.
-   [`ruff`](https://github.com/charliermarsh/ruff): linting.
-   [`mypy`](https://github.com/python/mypy): static type checking.
-   [`poetry`](https://github.com/python-poetry/poetry): package management.
-   [`pre-commit`](https://github.com/pre-commit/pre-commit): pre-commit hooks.
-   [`just`](https://github.com/casey/just): manage commands.
-   [`direnv`](https://github.com/direnv/direnv): autoloading vritual environment.

### Service/API

#### Google Cloud

1.  Create a [Google Cloud](https://cloud.google.com) account and a project.
2.  Set up a [Scheduler](https://cloud.google.com/secret-manager/docs/create-secret) for the daily
    cron job.
3.  Set up a [Pub/Sub](https://cloud.google.com/pubsub/docs/publish-receive-messages-console) topic.
4.  Install the [`gcloud`](https://cloud.google.com/sdk/gcloud) command line tool.

##### Architecture

The script itself is quite simple. Actually, more work is done on figuring out and setting up the
environment where it runs. I chose to deploy the bot on Google Cloud Functions (a serverless
platform). The following chart describe the overall architecture.

```mermaid
flowchart LR
    A("Daily Cron Jub<br>(Cloud Scheduler)")
    B("Topic<br>(Cloud Pub/Sub)")
    C("Bot Script<br>(Cloud Functions)")
    A -- publish --> B
    C -- subscribe --> B
```

The cron job will publish an event to the topic daily, triggering the bot function to execute its
logic to crawl the Round Up content from DefiLlama's website, extract relevant news, and then send
an excerpt to the channel.

#### Telegram

1. Create a [bot account](https://core.telegram.org/bots#how-do-i-create-a-bot).
2. Create a user account with [no-SIM signup](https://telegram.org/blog/ultimate-privacy-topics-2-0#sign-up-without-a-sim-card). (We'll be uploading the secret credentials to Google Cloud to log in as
   this user, so better not use the personal account.)
3. Follow the instructions from [Telethon](https://docs.telethon.dev/en/stable/concepts/sessions.html#string-sessions)
   to create session keys for both of the above accounts.

## Deploy

1.  `just deploy`: deploy the bot.
2.  `just trigger`: manually trigger the deployed bot (often used for testing).

> **Note**
> The first time deploying the bot to Google Cloud, some warnings and errors will pop up asking for
> permissions, e.g. granting default service account access to Secret Manager. Simply follow the
> hints and set up the required permissions to proceed.

## Contribution

Absolutely welcome. Also feel free to reach out to discuss the project or anything else!

## License

Dual licensed under either [MIT License](./LICENSE-MIT) or [Apache License, Version 2.0](./LICENSE-APACHE).
