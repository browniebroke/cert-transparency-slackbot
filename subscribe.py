from src import config, fb


def subscribe_domains():
    fb_client = fb.Client()
    for domain in config.DOMAINS_LIST:
        result = fb_client.subscribe(domain)
        print(f"Subscribed to {domain} = {result['success']}")


if __name__ == "__main__":
    subscribe_domains()
