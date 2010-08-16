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
from gaesessions import get_current_session
import os, binascii, authutil, logging

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


class register(webapp.RequestHandler):
	def get(self):
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
		path = os.path.join(os.path.dirname(__file__), 'templates/register.html')
		self.response.out.write(template.render(path, { 'keyline':keyline } ))
		

class transaction(webapp.RequestHandler):
	def post(self):
		session = get_current_session()
		id = self.request.get('id')
		dest = self.request.get('dest')
		quantity = "".join(self.request.get('quantity').split('.'))
		anticsrf = self.request.get('anticsrf')
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
		key = binascii.a2b_hex(results[0].enckey)
		#logging.info('data = %s' % binascii.b2a_hex(data))

		ct = authutil.encrypt_data(key,data)
		message = authutil.build_message(id, ct)
		message = binascii.b2a_base64(message).rstrip('\n')

		d = {'dest':dest, 'quantity':"%.2f" % (float(quantity)/100),'message':message}
		session['data']=d
		session['pin']='0'*(4-len(pin))+pin
		path = os.path.join(os.path.dirname(__file__), 'templates/transaction.html')
		self.response.out.write(template.render(path, d))


class validate(webapp.RequestHandler):
	def post(self):
		session = get_current_session()
		d = {'data':session['data']}
		pin = self.request.get('pin')
		if pin != session['pin']: d['success'] = 0
		else: d['success'] = 1
		session.terminate()
		path = os.path.join(os.path.dirname(__file__), 'templates/validate.html')
		self.response.out.write(template.render(path, d))


class reset(webapp.RequestHandler):
	def get(self):
		session = get_current_session()
		session.terminate()
		self.response.out.write("")

application = webapp.WSGIApplication(
	[('/register.*', register),
	('/transaction',transaction),
	('/validate',validate),
	('/.*', index)],
	debug=False)

def main():
	run_wsgi_app(application)

#if __name__ == "__main__":
#	main()
