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

import re

import flask
import flask.ext.yamlconfig
import requests
import twitter

app = flask.Flask(__name__)
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

flask.ext.yamlconfig.AppYAMLConfig(app, '../settings.yml')

app.route('/')(lambda: flask.redirect(flask.url_for('index')))

tco_uri_re = re.compile('https?://t\.co/[a-zA-Z0-9]{6,}')
twit = twitter.Twitter(
	auth=twitter.OAuth(
		app.config['TWITTER_API']['token'],
		app.config['TWITTER_API']['token_key'],
		app.config['TWITTER_API']['con_secret'],
		app.config['TWITTER_API']['con_secret_key']
	)
)

def get_redirects(tco_path):
	resp = requests.get('https://t.co/' + tco_path)
	if not resp.history:
		return
	urls = [r.url for r in resp.history]
	urls.append(resp.url)
	return urls

def get_status(tco_path):
	count = 20
	for scheme in ('http', 'https'):
		statuses = [ None ] * count
		while len(statuses) == count:
			results = twit.search.tweets(count=count, q="{0}://t.co/{1}".format(scheme, tco_path))
			statuses = results['statuses']
			for status in statuses:
				text = status['text']
				if tco_uri_re.search(text) is None:
					continue
				if text.startswith('RT @'):
					continue
				return status

@app.route('/index')
def index():
	jvars = {}
	tco_path = flask.request.args.get('q', '') or flask.request.args.get('tco_path', '')
	if tco_path.startswith('http://') or tco_path.startswith('https://'):
		tco_path = tco_path.split(':', 1)[-1][2:]
	if tco_path.startswith('t.co/'):
		tco_path = tco_path[5:]
	if re.match('^[a-zA-Z0-9]{6,20}$', tco_path):
		jvars['query'] = tco_path
		redirects = get_redirects(tco_path)
		jvars['redirects'] = redirects
		if redirects:
			jvars['status'] = get_status(tco_path)
	return flask.render_template('index.html', **jvars)
