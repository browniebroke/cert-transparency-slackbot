# Certificate Transparency Slackbot

<p align="center">
  <a href="https://github.com/browniebroke/cert-transparency-slackbot/actions?query=workflow%3ACI">
    <img alt="CI Status" src="https://img.shields.io/github/workflow/status/browniebroke/cert-transparency-slackbot/CI?label=CI&logo=github&style=flat-square">
  </a>
  <a href="https://codecov.io/gh/browniebroke/cert-transparency-slackbot">
    <img src="https://img.shields.io/codecov/c/github/browniebroke/cert-transparency-slackbot.svg?logo=codecov&style=flat-square" alt="Test coverage percentage">
  </a>
</p>
<p align="center">
  <a href="https://python-poetry.org/">
    <img src="https://img.shields.io/badge/packaging-poetry-299bd7?style=flat-square&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAASCAYAAABrXO8xAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAJJSURBVHgBfZLPa1NBEMe/s7tNXoxW1KJQKaUHkXhQvHgW6UHQQ09CBS/6V3hKc/AP8CqCrUcpmop3Cx48eDB4yEECjVQrlZb80CRN8t6OM/teagVxYZi38+Yz853dJbzoMV3MM8cJUcLMSUKIE8AzQ2PieZzFxEJOHMOgMQQ+dUgSAckNXhapU/NMhDSWLs1B24A8sO1xrN4NECkcAC9ASkiIJc6k5TRiUDPhnyMMdhKc+Zx19l6SgyeW76BEONY9exVQMzKExGKwwPsCzza7KGSSWRWEQhyEaDXp6ZHEr416ygbiKYOd7TEWvvcQIeusHYMJGhTwF9y7sGnSwaWyFAiyoxzqW0PM/RjghPxF2pWReAowTEXnDh0xgcLs8l2YQmOrj3N7ByiqEoH0cARs4u78WgAVkoEDIDoOi3AkcLOHU60RIg5wC4ZuTC7FaHKQm8Hq1fQuSOBvX/sodmNJSB5geaF5CPIkUeecdMxieoRO5jz9bheL6/tXjrwCyX/UYBUcjCaWHljx1xiX6z9xEjkYAzbGVnB8pvLmyXm9ep+W8CmsSHQQY77Zx1zboxAV0w7ybMhQmfqdmmw3nEp1I0Z+FGO6M8LZdoyZnuzzBdjISicKRnpxzI9fPb+0oYXsNdyi+d3h9bm9MWYHFtPeIZfLwzmFDKy1ai3p+PDls1Llz4yyFpferxjnyjJDSEy9CaCx5m2cJPerq6Xm34eTrZt3PqxYO1XOwDYZrFlH1fWnpU38Y9HRze3lj0vOujZcXKuuXm3jP+s3KbZVra7y2EAAAAAASUVORK5CYII=" alt="Poetry Badge">
  </a>
  <a href="https://github.com/ambv/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square" alt="Code style by Black">
  </a>
  <a href="https://github.com/pre-commit/pre-commit">
    <img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=flat-square" alt="pre-commit enabled">
  </a>
</p>

Uses [Facebook certificate alerts via webhook][fb-ct-webhook] to receive alerts and send them to Slack.

## Prerequisites

- Have an AWS account setup
- Have a Slack instance
- Have a Facebook account

## Deployment

These are the steps to get this serverless application deployed:

- Create a Slack app and install it on your Slack instance
- Create a Facebook app
- Configure secrets and deploy the serverless app to AWS
- Configure the Webhook product in Facebook to send alerts to the serverless function
- Subscribe to the domains you care about

### Set your local environment up

You should clone this repo and copy the `.env.example` as `.env`. This file is where you should keep your secrets, outside of source control.

Run `yarn install` to install all the [serverless framework][sls-home] dependencies. You'll need to have [Poetry] installed, check out their installation instructions if you don't have it. Then run `poetry install`.

### Set up Slack

You'll need to create [a Slack app][slack-apps] to send messages. You can give it a name like "Cert Transparency", icon and color. Then go over the "OAuth and permissions" section and select the following bot token scopes to the app: `chat.write` and `chat.write.public`.

Make sure to reinstall the app on your Slack instance. Copy the bot access token and set it as `SLACK_API_TOKEN` in your `.env` file.

While you're here, choose the channel where you want to receive the alerts, and set it as `SLACK_CHANNEL` in the `.env` file (with the leading `#`).

### Create a Facebook app

Create a Facebook app in your [developer dashboard][fb-apps], or use an existing one. Copy the App ID and secrets into your `.env` file.

### Other environment variables

Finally add the domains you want to received alerts for in the `DOMAINS_LIST` environment variables. The domains should be comma separated:

```
DOMAINS_LIST=facebook.com,google.com
```

### Deploy to AWS

Deploy your app to AWS with the profile and region that you want:

```
serverless deploy --region eu-west-2 --profile default
```

This should print out the URLs for the endpoints, you should see the same URL available for 2 HTTP verbs, GET and POST:

```
endpoints:
  POST - https://xxxxxxxxxx.execute-api.eu-west-2.amazonaws.com/dev
  GET - https://xxxxxxxxxx.execute-api.eu-west-2.amazonaws.com/dev
```

The endpoint is the URL where you'll receive the webhook from Facebook.

### Setup the Webhook

Go back to [your Facebook developers dashboard][fb-apps], and go into the app that you used earlier. Add the webhook product, and choose the Certificate Transparency. You should be prompted with a dialog asking for a callback URL as well as a verify token. The callback URL is the URL that was printed out at the end of the previous step and the verify token is `cert-transparency-slack`. Click verify and save.

Once the webhook is added, you can subscribe to 2 type of alerts: certificate or phishing alerts. Check out [the facebook documentation][fb-ct-webhook] to know more about each, this Slackbot only supports certificate for now.

### Subscribe your domains

The final step is to register the domains you want to receive alerts for. You can do so by running:

```
poetry run subscribe.py
```

This should print out the domains in your `.env` file as they are registered.

[poetry]: https://python-poetry.org/
[fb-ct-webhook]: https://developers.facebook.com/docs/certificate-transparency/#certificate-alerts
[sls-home]: https://www.serverless.com/
[fb-apps]: https://developers.facebook.com/apps/
[slack-apps]: https://api.slack.com/apps/
