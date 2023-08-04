#!/usr/bin/env python3
"""
Network connection tester
"""
import argparse
import json
import os
import logging
import sys

from enum import Enum
from pathlib import Path
from typing import List, Tuple
from urllib import request


LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


DEFAULT_TEST_URL = "https://api.gitguardian.com"

SCRIPT_DIR = Path(__file__).parent.absolute()

CACERT_PEM_PATH = SCRIPT_DIR / "cacert.pem"

SSL_TEST_URL = "https://www.howsmyssl.com/a/check"


class Mode(Enum):
    URLLIB = "urllib"
    REQUESTS = "requests"
    REQUESTS_OWN_CA = "requests-own-ca"


def send_get_urllib(url: str) -> Tuple[int, str]:
    response = request.urlopen(url)
    content = response.read().decode("utf-8", errors="backslashreplace")
    return response.status, content


def send_get_requests(url: str) -> Tuple[int, str]:
    response = requests.get(url)
    return response.status_code, response.text


def send_get_requests_own_ca(url: str) -> Tuple[int, str]:
    response = requests.get(url, verify=str(CACERT_PEM_PATH))
    return response.status_code, response.text


SEND_GET_FUNCTIONS = {
    Mode.URLLIB: send_get_urllib,
    Mode.REQUESTS: send_get_requests,
    Mode.REQUESTS_OWN_CA: send_get_requests_own_ca,
}


def run_test(test_url: str, mode: Mode) -> bool:
    logging.info("Testing mode=%s", mode.value)
    send_get = SEND_GET_FUNCTIONS[mode]

    try:
        logging.info("- Testing SSL",)
        status, content = send_get(SSL_TEST_URL)
        if status != 200:
            logging.error("Unexpected response. Status: %d", status)
            logging.error("Content: %s", content)
            return False
        dct = json.loads(content)
        logging.info(json.dumps(dct, indent=2))

        logging.info("- Testing url=%s", test_url)
        status, content = send_get(test_url)
    except Exception as e:
        logging.exception("Network error")
        return False

    if status != 200:
        logging.error("Unexpected response. Status: %d", status)
        logging.error("Content: %s", content)
        return False

    logging.info("OK")
    return True


def run_tests(test_url: str, modes: List[Mode]) -> int:
    ok = True
    for mode in modes:
        ok &= run_test(test_url, mode)

    return 0 if ok else 1


def main():
    mode_choices = [x.value for x in Mode]
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__
    )

    parser.add_argument(
        "-r", "--repeat", type=int, default=1, help="Repeat tests. Defaults to 1"
    )
    parser.add_argument("-m", "--mode", action="append", choices=mode_choices)
    parser.add_argument("test_url", nargs="?", default=DEFAULT_TEST_URL)

    args = parser.parse_args()
    if args.mode:
        modes = [Mode(x) for x in args.mode]
    else:
        modes = [Mode.URLLIB]

    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt="%H:%M:%S")

    if not CACERT_PEM_PATH.exists() and Mode.REQUESTS_OWN_CA in modes:
        logging.error("%s does not exist, can't use mode %s", str(CACERT_PEM_PATH), Mode.REQUESTS_OWN_CA.value)
        return 128

    if not REQUESTS_AVAILABLE and (Mode.REQUESTS in modes or Mode.REQUESTS_OWN_CA in modes):
        logging.error("`requests` is not available, can't test with %s", args.mode)
        return 128

    logging.info("Starting test using %s", args.test_url)

    errors = 0
    try:
        for idx in range(args.repeat):
            logging.info("Run %d/%d", idx + 1, args.repeat)
            errors += run_tests(args.test_url, modes)
    except KeyboardInterrupt:
        logging.info("Interrupted")

    logging.info("Errors: %d", errors)
    return errors


if __name__ == "__main__":
    sys.exit(main())
