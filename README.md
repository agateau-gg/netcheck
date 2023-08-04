# Netcheck

Netcheck is a simple network connection checker, used to troubleshoot network issues.

## Usage

- Clone the repository.
- Run `python netcheck.py`.

Netcheck uses `urllib` by default. To test with `requests`, run netcheck with `-m requests`.

To test with a separate CA:

- Download one in `cacert.pem` (or use `make cacert.pem` to have curl download its own CA for you)
- Run netcheck with `-m requests-own-ca`

To test reliability over multiple calls, use `-r N` where N is the number of times you want the check to be repeated.
