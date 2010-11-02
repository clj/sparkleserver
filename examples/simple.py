import os
import sys
sys.path.append('..')

from sparkleserver import sparkle_server

from wsgiref.simple_server import make_server

def simple_sparkle_server(environ, start_response):
    environ['sparkleserver.log.apache.path'] = 'logs/apache_style.log'
    environ['sparkleserver.feedpath'] = 'feeds/'
    environ['sparkleserver.log.sqlite.path'] = 'logs/log.sqlite'
    environ['sparkleserver.log.csv.path'] = 'logs/log.csv'
    return sparkle_server(environ, start_response)

try:
    os.mkdir('logs')
except OSError:
    pass

httpd = make_server('', 8000, simple_sparkle_server)
print "Serving on port 8000..."

# Serve until process is killed
httpd.serve_forever()
