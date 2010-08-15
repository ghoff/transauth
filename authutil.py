#  Copyright (C) 2010 Geoff Hoff, http://github.com/ghoff
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#  or download it from http://www.gnu.org/licenses/gpl.txt

import struct, binascii, dpd
from Crypto.Cipher import AES


def dataencode(account, amount, pin):
	""" Encode 31 base 10 numbers to 13 or fewer bytes and prefix with DP """
	data = dpd.dpdpack('0'*(16-len(account))+account+'0'*(11-len(amount))+amount+pin)
	data = "DPD" + binascii.a2b_hex(data)
	return(data)


def datadecode(input):
	""" Verify prefix DP and expand densely packed decimal """
	if input[:3] != "DPD":
		print "bad version number"
		return [0,0,0]
	data=binascii.b2a_hex(input[3:])
	data=dpd.dpdunpack(data)
	account=data[0:16]
	amount=data[16:27]
	pin=data[27:31]
	return([account, amount, pin])


def build_message(keyid, ciphertext):
	""" keyid 6 bytes, ciphertext 16 bytes """
	data = chr(2) + chr(0) + keyid + ciphertext
	return(data)


def split_message(data):
	offset = 0
	version = ord(data[offset]) + ord(data[offset+1])
	#TODO: do something with version
	offset += 2
	keyid = data[offset:offset+6]
	offset += 6
	crypt = data[offset:]
	return(keyid, crypt)


def encrypt_data(key, data):
	cipher = AES.new(key, AES.MODE_ECB)
	result = cipher.encrypt(data)
	return(result)


def decrypt_data(key, data):
	cipher = AES.new(key, AES.MODE_ECB)
	result = cipher.decrypt(data)
	return(result)


def test():
	pass

if __name__ == "__main__":
	test()
