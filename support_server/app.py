from contextlib import contextmanager
import logging
import sys
from threading import Lock
from time import sleep
from typing import Any, Iterator, Optional, Tuple, Union

import click
from flask import Flask, jsonify, request
from seleniumwire import webdriver # type: ignore
from selenium.common.exceptions import TimeoutException, InvalidArgumentException, UnexpectedAlertPresentException
from selenium.webdriver.firefox.options import Options
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

class DriverPool:
    lock = Lock()
    retries = 4
    retry_wait = .5

    def __init__(self, n_drivers: int, headless: bool = True) -> None:
        options = Options()
        options.headless = headless
        options.set_preference('dom.webnotifications.enabled', False)
        self.drivers = [webdriver.Firefox(options=options) for _ in range(n_drivers)]
    
    @contextmanager
    def _get_free_driver(self) -> Iterator[Optional[webdriver.Firefox]]:
        for _ in range(self.retries):
            try:
                driver = self.drivers.pop()
                break
            except IndexError:
                sleep(self.retry_wait)
        else:
            driver = None

        try:
            yield driver
        finally:
            if driver is not None:
                self.drivers.append(driver)

    def get(self, url: str, identikey: str) -> str:
        with self._get_free_driver() as driver:
            if driver is None:
                return 'busy'

            # Load for 6 seconds at max. Why 6? Made it up. Everything should be <10ms, unless
            # someone put an infinite redirect in their XSS or something.
            driver.set_page_load_timeout(6)
            try:
                # Set the StudentIdentikey header for all outgoing requests
                def interceptor(request: Any) -> None:
                    request.headers['StudentIdentikey'] = identikey

                driver.request_interceptor = interceptor
                # Get the URL. This might fail if the previous student has an alert popup open, so
                # we catch that error and retry until it works. I don't think this is possible to
                # loop infinitely, but maybe. Hasn't happened yet.
                while True:
                    try:
                        driver.get(url)
                        break
                    except UnexpectedAlertPresentException:
                        pass
            except InvalidArgumentException:
                log.exception('Bad url')
                return 'The URL was invalid'
            except TimeoutException:
                log.exception('Timeout')
                driver.get('')
                return 'timeout'

            return 'success'


drivers: DriverPool = None # type: ignore

@app.route('/')
def index() -> View:
    return 'ok'

@app.route('/visit')
def visit() -> View:
    url = request.json.get('url') # type: ignore
    identikey = request.json.get('identikey') # type: ignore

    if not url or not identikey:
        log.error('Did not get URL or identikey')

        # This should never happen unless there is a bug somewhere
        return jsonify({ 'status': 'internal error (reach out to instructor)' }) # type: ignore

    log.info('{} requested URL: {}'.format(identikey, url))
    status = drivers.get(url, identikey)

    return jsonify({ 'status': status }) # type: ignore

@click.command()
@click.option('--debug', is_flag=True)
@click.option('--port', type=int, default=8082)
def main(debug: bool, port: int) -> None:
    global drivers
    if debug:
        # When running locally, a single browser with the UI enabled is fine
        log.setLevel(logging.DEBUG)
        drivers = DriverPool(1, headless=False)
    else:
        # When running in prod, use 5 headless browsers for concurrency
        drivers = DriverPool(5)

    log.info('Starting support server on http://127.0.0.1:{}'.format(port))

    app.run(threaded=True, debug=debug, port=port)

if __name__ == '__main__':
    main()