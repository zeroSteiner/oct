#!/usr/bin/python -B
# -*- coding: utf-8 -*-

import argparse
import os
import requests

try:
	import readline
except ImportError:
	pass
else:
	import rlcompleter
	readline.parse_and_bind('tab: complete')

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
	import oct
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
