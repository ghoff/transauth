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

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch
from gaesessions import get_current_session
from django.utils import simplejson
import os, binascii, authutil, logging, string, base64
import urllib, recaptcha


def validate_input(allowed, inp):
	if allowed == None:
		allowed = string.ascii_letters + string.digits + "-_"
	inp = inp.encode('UTF-8')
	delete_table = string.maketrans(allowed, ' ' * len(allowed))
	table = string.maketrans('', '')
	return(inp.translate(table, delete_table))


class transdata(db.Model):
	id = db.IntegerProperty(required=True)
	enckey = db.StringProperty(required=True)


class index(webapp.RequestHandler):
	def get(self):
		session = get_current_session()
		anticsrf = binascii.b2a_hex(os.urandom(16))
		session['anticsrf'] = anticsrf
		path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
		self.response.out.write(template.render(path, { 'anticsrf':anticsrf } ))


class transaction(webapp.RequestHandler):
	def get(self):
		self.post()
	def post(self):
		session = get_current_session()
		allowed = string.digits
		id = validate_input(allowed, self.request.get('id'))
		if len(id) > 3:
			self.response.out.write('id too long!!')
			return
		dest = validate_input(allowed, self.request.get('dest'))
		if len(dest) > 16:
			self.response.out.write('destination account too long!!')
			return

		dollarscents = validate_input(allowed + ".", self.request.get('quantity')).split('.')
		if len(dollarscents) > 2:
			self.response.out.write('bad quantity!!')
			return
		if len(dollarscents[0]) > 9:
			self.response.out.write('quantity too large!!')
			return
		if len(dollarscents) == 1:
			dollarscents.append("00")
		cenlen = len(dollarscents[1])
		if (cenlen > 2):
			quantity = dollarscents[0] + dollarscents[1][:2]
		else:
			quantity = dollarscents[0] + dollarscents[1] + '0' * (2 - cenlen)

		anticsrf = validate_input(string.hexdigits, self.request.get('anticsrf'))
		if anticsrf != session['anticsrf']:
			self.response.out.write('bad session!!')
			return

		#import struct
		#pin = str(struct.unpack('H',os.urandom(2))[0]%10000)
		pin = str(int(binascii.b2a_hex(os.urandom(2)),16) % 10000)
		data = authutil.dataencode(dest,quantity,pin)

		query = transdata.all()
		query.filter('id =', int(id)) 
		results = query.fetch(limit=1)
		if len(results) != 1:
			self.response.out.write('bad id!!')
			return

		key = binascii.a2b_hex(results[0].enckey)
		#logging.info('data = %s' % binascii.b2a_hex(data))

		ct = authutil.encrypt_data(key,data)
		message = authutil.build_message(id, ct)
		message = base64.urlsafe_b64encode(message)

		d = {'dest':dest, 'quantity':"%.2f" % (float(quantity)/100),'message':message}
		session['data']=d
		session['pin']='0'*(4-len(pin))+pin
		path = os.path.join(os.path.dirname(__file__), 'templates/transaction.html')
		self.response.out.write(template.render(path, d))


class validate(webapp.RequestHandler):
	def post(self):
		session = get_current_session()
		d = {'data':session['data']}
		pin = validate_input(string.digits, self.request.get('pin'))
		if len(pin) > 4:
			self.response.out.write('pin too long!!')
			return
		if pin != session['pin']: d['success'] = 0
		else: d['success'] = 1
		session.terminate()
		path = os.path.join(os.path.dirname(__file__), 'templates/validate.html')
		self.response.out.write(template.render(path, d))


class register(webapp.RequestHandler):
	def post(self):
		result = self.checkcaptcha()
		if result[0] != 'true':
			if self.request.get('ajax'):
				self.response.headers.add_header("Content-Type", "application/json")
				self.response.out.write(simplejson.dumps({'error':1}))
				return
			else:
				d = { 'key': recaptcha.public_key, 'error' : "&error=%s" % result[1] }
				path = os.path.join(os.path.dirname(__file__), 'templates/register.html')
				self.response.out.write(template.render(path, d))
				return

		query = transdata.all()
		query.order('-id')
		results = query.fetch(limit=1)
		if len(results) == 0:
			id = 1
		else:
			id = results[0].id + 1
		newkey = binascii.b2a_hex(os.urandom(16))
		keydata = transdata(id=id, enckey=newkey)
		keydata.put()
		keyline = '%d, %s' % (id,newkey)
		if self.request.get('ajax'):
			self.response.headers.add_header("Content-Type", "application/json")
			self.response.out.write(simplejson.dumps({'error':0,'keyline':keyline}))
		else:
			path = os.path.join(os.path.dirname(__file__), 'templates/register2.html')
			self.response.out.write(template.render(path, { 'keyline':keyline } ))


	def get(self):
		d = { 'key': recaptcha.public_key }
		path = os.path.join(os.path.dirname(__file__), 'templates/register.html')
		self.response.out.write(template.render(path, d))


	def checkcaptcha(self):
		recaptcha_challenge_field = self.request.get('recaptcha_challenge_field')
		recaptcha_response_field = self.request.get('recaptcha_response_field')
		if len(recaptcha_challenge_field)==0 or len(recaptcha_response_field)==0:
			return ['false', 'incorrect-captcha-sol']
		ip = self.request.remote_addr
		#logging.info('recaptcha_challenge_field=%s' % recaptcha_challenge_field)
		#logging.info('recaptcha_response_field=%s' % recaptcha_response_field)
		params = urllib.urlencode({ 'remoteip': ip,
			'privatekey':recaptcha.private_key,
			'challenge': recaptcha_challenge_field,
			'response': recaptcha_response_field})
		result = urlfetch.fetch(url="http://www.google.com/recaptcha/api/verify",
			payload=params, method=urlfetch.POST,
			headers={'Content-Type': 'application/x-www-form-urlencoded'})
		return(result.content.splitlines())


#class reset(webapp.RequestHandler):
#	def get(self):
#		session = get_current_session()
#		session.terminate()
#		self.response.out.write("")

application = webapp.WSGIApplication(
	[('/register', register),
	('/transaction',transaction),
	('/validate',validate),
	('/', index)],
	debug=False)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()
