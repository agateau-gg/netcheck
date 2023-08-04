all: netcheck.zip


netcheck.zip: cacert.pem
	cd .. && zip -r netcheck/netcheck.zip netcheck/netcheck.py netcheck/cacert.pem


cacert.pem:
	curl --remote-name https://curl.se/ca/cacert.pem


clean:
	rm -f netcheck.zip cacert.pem
