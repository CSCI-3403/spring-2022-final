import re
from typing import Optional
from urllib.parse import urlparse

import requests

SUPPORT_URL = 'http://127.0.0.1:8082'
URL_REGEX = r'(https?://)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)'

def find_link(message: str) -> Optional[str]:
    match = re.match(URL_REGEX, message)

    if not match:
        return None
    
    url = match.group(0)

    if url.startswith('http://') or url.startswith('https://'):
        return url
    else:
        return 'http://' + url

def handle_message(message: str, identikey: str) -> str:
    url = find_link(message)

    if not url:
        return 'I do not understand. Can you send me a link to the page you are having problems with?'
    
    if urlparse(url).netloc != 'final.csci3403.com':
        return 'I\'m sorry, but I will only visit URLs from final.csci3403.com.'

    response = requests.get('{}/visit'.format(SUPPORT_URL), json={
        'url': url,
        'identikey': identikey
    })

    if not 200 <= response.status_code < 300:
        return 'I tried visiting {}, but there was some kind of error'.format(url)

    status = response.json().get('status')

    if status == 'success':
        return 'I just visited {}!'.format(url)
    elif status == 'timeout':
        return 'I tried to visit {}, but it took too long to load'.format(url)
    elif status == 'busy':
        return 'Sorry, I am very busy at the moment. Can you send that again in a moment?'
    else:
        return 'I tried visiting {}, but failed to load it: {}'.format(url, status)
