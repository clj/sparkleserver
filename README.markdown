# Sparle Server

>> Christian Jacobsen  
>>   <http://christian.lyderjacobsen.org/>  
>>   <http://www.absolutepanic.org/>

A Python/WSGI based webservice that serves up appcasts for Sparkle (and
anything else really) with support for logging reported system configurations
in various formats: csv, apache style log, sqlite database.

## License

The server is distributed under a BSD-style license.

## Files

* `sparkleserver.py`  
  The WSGI application.

* `appcast.wsgi`  
  An example of how to configure and run the webservice for use with
    [mod\_wsgi][mod_wsgi]

## Use and Configuration

To use sparkleserver you need a [wsgi][] compatible webserver. You
have a number of choices including [wsgiref.simple\_server][wsgisimple] and
[mod\_wsgi][mod_wsgi]. This documentation will show you how to set up the
latestversionserver using these two wsgi servers.

### wsgiref.simple_server

`wsgiref` is a standard python module as of Python 2.5. You can use this server
to test and experiment with the server. An example of how to configure the
server can be seen at the bottom of the `sparkleserver.py` file and more
help can be found in the [relevant Python documentation][wsgisimple]. 

### mod_wsgi

Serving using [mod\_wsgi][mod_wsgi] is not too different from with
wsgiref.simple_server. An example can be found in `appcast.wsgi`.

## Configuration

The configuration of the webservice happens by passing a number of variables
using the environ variable. See `appcast.wsgi` and the bottom of
`sparkleserver.py` for an example of how to do this.

### Configuration keys

The following key is mandatory in the environment:

* `sparkleserver.feedpath`  
  Sets the location of a path from which to serve feeds. This should be a
  directory in which one or more appcast feeds are located.

The following keys are optional:

* `sparkleserver.log.apache.path`  
  The full path to a file in which an apache style log should be created (this
  file is appended to). All requests will be logged in this file.
* `sparkleserver.log.sqlite.path`  
  The fill path to a sqlite database in which the system profiling information
  will be stored. This file does not have to exist, and will be created as
  necessary. Only requests which send profiling data will be logged in this
  file.
* `sparkleserver.log.csv.path`  
  The fill path to a csv file in which the system profiling information
  will be stored. This file does not have to exist, and will be created as
  necessary. Only requests which send profiling data will be logged in this
  file.
 
## Using the webservice

Simply set the `SUFeedURL` to the location where you have started the
sparkleserver instance. If you wish to gather information about your users
systems, be sure to enable `SUEnableSystemProfiling` and enable logging of the
data in a format that suits your needs.

[wsgi]:        http://wsgi.org/wsgi/
[mod_wsgi]:    http://code.google.com/p/modwsgi/
[wsgisimple]:  http://docs.python.org/library/wsgiref.html#module-wsgiref.simple_server
