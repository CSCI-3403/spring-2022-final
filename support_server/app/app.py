import logging
import socket
import sys
from typing import Any, Dict, Tuple, Union

import click
from flask import abort, Flask, render_template, request
from seleniumwire import webdriver # type: ignore
from selenium.common.exceptions import TimeoutException, InvalidArgumentException, InvalidSessionIdException
from werkzeug.wrappers import Response

View = Union[Response, str, Tuple[str, int]]

log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger('werkzeug').disabled = True
logging.getLogger('seleniumwire.storage').disabled = True
logging.getLogger('seleniumwire.backend').disabled = True
logging.getLogger('seleniumwire.handler').disabled = True
logging.getLogger('seleniumwire.server').disabled = True


# Set up app
app = Flask(__name__)

# SeleniumWire forwards web requests through a local proxy, which is how it modifies requests.
# Because we are running SeleniumWire in a separate container from the actual browser, we need to
# manually specify that requests should be proxied through this container.
ip_addr = socket.gethostbyname(socket.gethostname())
seleniumwire_options = {
    'addr': ip_addr,
    # 'port': 3128,
}

firefox_options = webdriver.FirefoxOptions()
firefox_options.set_capability('unhandledPromptBehavior', 'dismiss')

def build_driver():
    driver = webdriver.Remote(
        command_executor='http://webdriver:4444',
        seleniumwire_options=seleniumwire_options,
        options=firefox_options,
    )
    driver.set_page_load_timeout(3)
    return driver

driver = build_driver()
    
def get(url: str, headers: Dict[str, str]) -> None:
    global driver

    try:
        # Set the StudentIdentikey header for all outgoing requests
        def interceptor(request: Any) -> None:
            for k, v in headers.items():
                request.headers[k] = v

        driver.request_interceptor = interceptor
        driver.get(url)

    except InvalidArgumentException as e:
        log.exception("Invalid URL")
        abort(400, 'Invalid URL')
    except TimeoutException as e:
        log.exception("Timeout")
        abort(400, 'Request took too long, and timed out')
    except Exception as e:
        log.exception("Generic exception")
        abort(500, f'Internal server error: {e}')

@app.route('/')
def index() -> View:
    return render_template("index.html")

@app.route('/visit', methods=["POST"])
def visit() -> View:
    url = request.json.get('url') # type: ignore
    headers = request.json.get('headers', {}) # type: ignore

    if not url:
        abort(400, "Missing required URL parameter")

    get(url, headers)

    return "Success"

@click.command()
@click.option('--debug', is_flag=True)
@click.option('--port', type=int, default=80)
def main(debug: bool, port: int) -> None:
    log.info('Starting support server on http://0.0.0.0:{}'.format(port))

    app.run("0.0.0.0", debug=debug, port=port)

if __name__ == '__main__':
    main()