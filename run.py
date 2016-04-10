#!/usr/bin/python -B
# -*- coding: utf-8 -*-
#
#  run.py
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

import argparse
import os
import requests

import oct

try:
	import readline
except ImportError:
	pass
else:
	import rlcompleter
	readline.parse_and_bind('tab: complete')

app = oct.app

def main():
	parser = argparse.ArgumentParser(description='OCT', conflict_handler='resolve')
	parser.add_argument('-v', '--version', action='version', version=parser.prog + ' Version: 1.0')
	subparsers = parser.add_subparsers(dest='action', help='action')

	parser_serve = subparsers.add_parser('serve', help='start a development server')
	parser_serve.add_argument('-a', '--address', dest='address', default=None, help='the address to bind to')
	parser_serve.add_argument('-p', '--port', dest='port', default=5000, type=int, help='the port to bind to')

	parser_search = subparsers.add_parser('search', help='run a quick search')
	parser_search.add_argument('tco_path', help='the target t.co uri path')

	arguments = parser.parse_args()
	if arguments.action == 'serve':
		if os.environ.get('DISPLAY'):
			if not 'X-RUN-CHILD' in os.environ:
				os.system("gvfs-open http://{0}:{1}/".format(arguments.address or 'localhost', arguments.port))
				os.environ['X-RUN-CHILD'] = 'X'
		oct.app.run(host=arguments.address, port=arguments.port, debug=True)
	elif arguments.action == 'search':
		tco_path = arguments.tco_path
		redirects = oct.get_redirects(tco_path)
		if not redirects:
			print("[-] https://t.co/{0} does not redirect".format(tco_path))
			return 0
		print('redirects:')
		for url in redirects:
			print('  ' + url)

		status = oct.get_status(tco_path)
		if status is None:
			print('[-] failed to find status for https://t.co/' + tco_path)
			return 0
		print('status:')
		print("  https://twitter.com/{0}/status/{1} (fav:{2:,} re:{3:,})".format(status['user']['screen_name'], status['id'], status['favorite_count'], status['retweet_count']))
		print('  ' + status['user']['name'])
		print('  ' + status['text'])
	return 0

if __name__ == '__main__':
	main()
