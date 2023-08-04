#!/usr/bin/env python3
"""
Network connection tester
"""
import argparse
import os
import logging
import sys

from pathlib import Path
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


def run_test(url, *, use_requests=True, verify=True):
    try:
        if use_requests:
            logging.info("Testing with requests (verify=%s)", verify)
            response = requests.get(url, verify=verify)
            status = response.status_code
            content = response.text
        else:
            logging.info("Testing with urllib")
            response = request.urlopen(url)
            status = response.status
            content = response.read().decode("utf-8", errors="backslashreplace")
    except Exception as e:
        logging.exception("Network error")
        return False

    if status != 200:
        logging.error("Unexpected response. Status: %d", status)
        logging.error("Content: %s", content)
        return False

    logging.info("OK")
    return True


def run_tests(test_url) -> int:
    ok = True
    if REQUESTS_AVAILABLE:
        ok &= run_test(test_url, use_requests=True, verify=True)
        ok &= run_test(test_url, use_requests=True, verify=False)
        if CACERT_PEM_PATH.exists():
            logging.info("Defining REQUESTS_CA_BUNDLE to %s", str(CACERT_PEM_PATH))
            os.environ["REQUESTS_CA_BUNDLE"] = str(CACERT_PEM_PATH)
            ok &= run_test(test_url, use_requests=True, verify=True)
            del os.environ["REQUESTS_CA_BUNDLE"]
    ok &= run_test(test_url, use_requests=False)

    return 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__
    )

    parser.add_argument(
        "-r", "--repeat", type=int, default=1, help="Repeat tests. Defaults to 1"
    )
    parser.add_argument("test_url", nargs="?", default=DEFAULT_TEST_URL)

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt="%H:%M:%S")

    if not CACERT_PEM_PATH.exists():
        logging.warning("%s does not exist, not testing with it", str(CACERT_PEM_PATH))

    if not REQUESTS_AVAILABLE:
        logging.warning("`requests` is not available, not testing with it")

    logging.info("Starting test using %s", args.test_url)

    errors = 0
    try:
        for idx in range(args.repeat):
            logging.info("Run %d/%d", idx + 1, args.repeat)
            errors += run_tests(args.test_url)
    except KeyboardInterrupt:
        logging.info("Interrupted")

    logging.info("Errors: %d", errors)
    return errors


if __name__ == "__main__":
    sys.exit(main())
