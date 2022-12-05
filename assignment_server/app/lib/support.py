import re
from typing import Optional
from urllib.parse import urlparse

import requests

SUPPORT_URL = 'http://support'
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
        return 'I\'m sorry, I do not understand. Can you send me a link to the page you are having problems with?'
    
    response = requests.post('{}/visit'.format(SUPPORT_URL), json={
        'url': url,
        'headers': {
            'StudentIdentikey': identikey,
        }
    })

    return 'I just visited {}! Boy do I love clicking suspicious links.'.format(url)
    # if not 200 <= response.status_code < 300:
    #     return 'I tried visiting {}, but there was some kind of error. Please try again.'.format(url)
    # else:
    #     return 'I just visited {}! Boy do I love clicking suspicious links.'.format(url)
