from typing import List
import click
import requests

def challenges(host: str, port: int) -> None:
    response = requests.post(f'http://{host}:{port}/challenges')
    response.raise_for_status()
    print(response.json())

def score(host: str, port: int) -> None:
    response = requests.post(f'http://{host}:{port}/score/test_student')
    response.raise_for_status()
    print(response.json())

def update(host: str, port: int) -> None:
    response = requests.post(f'http://{host}:{port}/update/test_student2', json={
        'challenge': 1,
        'comment': 'asdf'
    })
    response.raise_for_status()
    print(response.json())

@click.command()
@click.option('--host', type=str, default='localhost')
@click.option('--port', type=int, default=8081)
@click.argument('endpoint')
def main(host: str, port: int, endpoint: str) -> None:
    if endpoint == 'challenges':
        challenges(host, port)
    elif endpoint == 'score':
        score(host, port)
    elif endpoint == 'update':
        update(host, port)
    else:
        print('[!] Unknown endpoint, choose one of ["challenges", "score"]')

if __name__ == '__main__':
    main()