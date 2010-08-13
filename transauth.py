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
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from gaesessions import get_current_session

class index(webapp.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		session = get_current_session()
		if "count" in session:
			self.response.out.write(str(session["count"])+"<br>\n")
			if session["count"] == 30: self.response.out.write("you win<br>\n")
			session["count"] += 1
		else:
			session["count"] = 1
		self.response.out.write("hello world<br>\n")
		self.response.out.write('<a href="reset">reset</a>')

class reset(webapp.RequestHandler):
	def get(self):
		session = get_current_session()
		session.terminate()
		self.response.out.write("")

application = webapp.WSGIApplication(
	[('/reset.*', reset),
	('/.*', index)],
	debug=False)

def main():
	run_wsgi_app(application)

#if __name__ == "__main__":
#	main()
