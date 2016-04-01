#!/usr/bin/python -B
# -*- coding: utf-8 -*-
#
#  __init__.py
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following disclaimer
#    in the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of the  nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import datetime
import re

import flask
import flask.ext.sqlalchemy
import requests
import sqlalchemy.dialects.postgresql as postgresql
import twitter

app = flask.Flask(__name__)
app.config.from_object('oct.default_settings')
app.config.from_pyfile('application.cfg', silent=True)
app.config.from_envvar('OCT_SETTINGS', silent=True)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

sqlalchemy = flask.ext.sqlalchemy.SQLAlchemy(app)

tco_uri_re = re.compile('https?://t\.co/[a-zA-Z0-9]{6,}')
twit = twitter.Twitter(
	auth=twitter.OAuth(
		app.config['TWITTER_API']['token'],
		app.config['TWITTER_API']['token_key'],
		app.config['TWITTER_API']['con_secret'],
		app.config['TWITTER_API']['con_secret_key']
	)
)

class SearchResult(sqlalchemy.Model):
	__tablename__ = 'search_results'
	id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
	created = sqlalchemy.Column(sqlalchemy.DateTime, default=lambda _: datetime.datetime.utcnow())
	path = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
	queried_count = sqlalchemy.Column(sqlalchemy.Integer, default=1)
	redirects = sqlalchemy.Column(postgresql.JSON, nullable=False)
	status = sqlalchemy.Column(postgresql.JSON, nullable=False)
	def __repr__(self):
		return "<search_result id:{0} path:\"{1}\" >".format(self.id, self.path)

sqlalchemy.create_all()

def get_redirects(tco_path):
	try:
		resp = requests.get('https://t.co/' + tco_path)
	except requests.exceptions.RequestException:
		return
	if not resp.history:
		return
	urls = [r.url for r in resp.history]
	urls.append(resp.url)
	return urls

def get_status(tco_path):
	count = 20
	for scheme in ('http', 'https'):
		statuses = [None] * count
		while len(statuses) == count:
			try:
				results = twit.search.tweets(count=count, q="{0}://t.co/{1}".format(scheme, tco_path))
			except twitter.TwitterHTTPError:
				return
			statuses = results['statuses']
			for status in statuses:
				text = status['text']
				if tco_uri_re.search(text) is None:
					continue
				if 'retweeted_status' in status:
					return status['retweeted_status']
				return status

@app.route('/')
def index():
	jvars = {}
	tco_path = flask.request.args.get('q', '') or flask.request.args.get('tco_path', '')
	if tco_path.startswith('http://') or tco_path.startswith('https://'):
		tco_path = tco_path.split(':', 1)[-1][2:]
	if tco_path.startswith('t.co/'):
		tco_path = tco_path[5:]

	if re.match('^[a-zA-Z0-9]{6,20}$', tco_path):
		session = sqlalchemy.session
		jvars['query'] = tco_path
		search_result = session.query(SearchResult).filter_by(path=tco_path).first()
		if search_result is None:
			redirects = get_redirects(tco_path)
			if redirects:
				jvars['redirects'] = redirects
				status = get_status(tco_path)
				if status is not None:
					search_result = SearchResult(path=tco_path, redirects=redirects, status=status)
					session.add(search_result)
		else:
			search_result.queried_count += 1

		if search_result is not None:
			jvars['redirects'] = search_result.redirects
			jvars['status'] = search_result.status
			session.commit()
	return flask.render_template('index.html', **jvars)
