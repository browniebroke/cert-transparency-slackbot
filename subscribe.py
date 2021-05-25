import sys

from src import fb


def subscribe_domains(domain):
    fb_client = fb.Client()
    result = fb_client.subscribe(domain)
    print(f"Subscribed to {domain} = {result['success']}")


if __name__ == "__main__":
    subscribe_domains(sys.argv[1])
