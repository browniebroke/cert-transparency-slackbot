from environs import Env

env = Env()
env.read_env()

FACEBOOK_APP_ID = env("FACEBOOK_APP_ID", "")
FACEBOOK_APP_SECRET = env("FACEBOOK_APP_SECRET", "")

SLACK_API_TOKEN = env("SLACK_API_TOKEN", "")
SLACK_CHANNEL = env("SLACK_CHANNEL", "")

DOMAINS_LIST = env.list("DOMAINS_LIST", "")

SENTRY_DSN = env("SENTRY_DSN", "")
