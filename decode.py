#!/usr/bin/env python

import authutil, binascii, sys, base64


def main():
	keys = {}
	if len(sys.argv) != 2:
		print "message be first and only argument"
		return(-1)

	fp = open('keys.list')
	for line in fp:
		keyid, key = line.split(',')
		keys[keyid] = key.strip()

	message = base64.urlsafe_b64decode(sys.argv[1])
	kid, ct = authutil.split_message(message)
	kid = kid.lstrip('0')
	key = binascii.a2b_hex(keys[kid])
	pt = authutil.decrypt_data(key, ct)
	acct, amount, pin = authutil.datadecode(pt)

	print "Destination account number is: " + acct.lstrip('0')
	print "Amount to be transfered: %.2f" % (float(amount)/100)
	print "Please enter pin %s to verify transaction" % pin
	return(0)


if __name__ == "__main__":
	exit(main())
