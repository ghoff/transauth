import os
import binascii
from gaesessions import SessionMiddleware
COOKIE_KEY= binascii.a2b_hex('a91944cbbb2bd9100bc9693901191bdf265b9af10d10162e3900774bb2e362c868f0f7bbee80911c9b9bce3d1b4ae8306bf3a5a8421aeca15056217f3259df1d')

def webapp_add_wsgi_middleware(app):
  from google.appengine.ext.appstats import recording
  app = recording.appstats_wsgi_middleware(app)
  app = SessionMiddleware(app, cookie_key=COOKIE_KEY, cookie_only_threshold=0,
	no_datastore=True)
  return app

