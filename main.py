#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import cgi
import datetime
import urllib
import webapp2

from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.api import users


class Greeting(db.Model):
    """Models a Guestbook entry with an author, content, avatar, and date."""
    author = db.StringProperty()
    content = db.StringProperty(multiline=True)
    avatar = db.BlobProperty()
    date = db.DateTimeProperty(auto_now_add=True)


def guestbook_key(guestbook_name=None):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return db.Key.from_path('Guestbook', guestbook_name or 'default_guestbook')


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('<html><body>')
        guestbook_name=self.request.get('guestbook_name')

        greetings = db.GqlQuery('SELECT * '
                                'FROM Greeting '
                                'WHERE ANCESTOR IS :1 '
                                'ORDER BY date DESC LIMIT 10',
                                guestbook_key(guestbook_name))

        for greeting in greetings:
            if greeting.author:
                self.response.out.write(
                    '<b>%s</b> wrote:' % greeting.author)
            else:
                self.response.out.write('An anonymous person wrote:')
            self.response.out.write('<div><img src="img?img_id=%s"></img>' %
                                    greeting.key())
            self.response.out.write('<blockquote>%s</blockquote></div>' %
                                    cgi.escape(greeting.content))

        self.response.out.write("""
                <form action = "/getOpenId" method="post">
                    <button name="openId" value="https://openid.nus.edu.sg" class="btn btn-primary btn-lg" type = "submit"><font><font>Login with IVLE</font></font></button>
                </form>
              <form action="/sign?%s" enctype="multipart/form-data" method="post">
                <div><textarea name="content" rows="3" cols="60"></textarea></div>
                <div><label>Avatar:</label></div>
                <div><input type="file" name="img"/></div>
                <div><input type="submit" value="Sign Guestbook"></div>
              </form>
              <hr>
              <form>Guestbook name: <input value="%s" name="guestbook_name">
              <input type="submit" value="switch"></form>
            </body>
          </html>""" % (urllib.urlencode({'guestbook_name': guestbook_name}),
                        cgi.escape(guestbook_name)))

class GetOpenId(webapp2.RequestHandler):
    def post(self):
        openId = self.request.get('openId').rstrip()
        self.redirect(users.create_login_url('/',None, federated_identity=openId))

class Image(webapp2.RequestHandler):
    def get(self):
        greeting = db.get(self.request.get('img_id'))
        if greeting.avatar:
            self.response.headers['Content-Type'] = 'image/png'
            self.response.out.write(greeting.avatar)
        else:
            self.response.out.write('No image')


class Guestbook(webapp2.RequestHandler):
    def post(self):
        guestbook_name = self.request.get('guestbook_name')
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.author = users.get_current_user().nickname()

        greeting.content = self.request.get('content')
        avatar = images.resize(self.request.get('img'), 32, 32)
        greeting.avatar = db.Blob(avatar)
        greeting.put()
        self.redirect('/?' + urllib.urlencode(
            {'guestbook_name': guestbook_name}))


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/img', Image),
                               ('/sign', Guestbook),
                               ('/getOpenId', GetOpenId),],
                              debug=True)