import sys
sys.path.append('..')

from sparkleserver import sparkle_server

from wsgiref.simple_server import make_server

def cumulative_sparkle_server(environ, start_response):
    environ['sparkleserver.cumulative'] = [
            dict(feed='testapp.xml',
                 feedpath='cumulative/testapp.xml',
                 changelogpath='cumulative/changes', 
                 appname='Test App')
            ]
    return sparkle_server(environ, start_response)

httpd = make_server('', 8000, cumulative_sparkle_server)
print "Serving on port 8000..."

# Serve until process is killed
httpd.serve_forever()
