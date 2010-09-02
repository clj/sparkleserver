from sparkleserver import sparkle_server

def configured_sparkle_server(environ, start_response):
    environ['sparkleserver.log.apache.path'] = \
      '/sparkleserver/amazingapp/logs/apache_style.log'
    environ['sparkleserver.feedpath'] = \
      '/sparkleserver/amazingapp/feeds/'
    environ['sparkleserver.log.sqlite.path'] = \
      '/sparkleserver/amazingapp/logs/log.sqlite'
    environ['sparkleserver.log.csv.path'] = \
      '/sparkleserver/amazingapp/logs/log.csv'
    return sparkle_server(environ, start_response)
    
application = configured_sparkle_server
