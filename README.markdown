# Sparle Server

>> Christian Jacobsen  
>>   <http://christian.lyderjacobsen.org/>  
>>   <http://www.absolutepanic.org/>

A Python/WSGI based webservice that serves up appcasts for Sparkle (and
anything else really) with support for cumulative changelogs and logging
reported system configurations in various formats: csv, apache style log,
sqlite database.

## License

The server is distributed under a BSD-style license.

## Files

* `sparkleserver.py`  
  The WSGI application.

* `appcast.wsgi`  
  An example of how to configure and run the webservice for use with
    [mod\_wsgi][mod_wsgi]

## Use and configuration

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
using the environ variable. See `appcast.wsgi`, `cumulative.py`, and `simple.py` in the examples directory for examples of how to do this.

### Configuration keys

At least one of the following keys must be present:

* `sparkleserver.feedpath`  
  Sets the location of a path from which to serve feeds. This should be a
  directory in which one or more appcast feeds are located.
* `sparkleserver.cumulative`  
  A dictionary containing the configuration for the feeds using cumulative 
  logs. See the specific documentation on cumulative setup later.

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

## Cumulative setup

It is currently only possible to have one cumulative feed per sparkleserver. This feed is described with a dictionary containing the following keys: `feed`, `feedpath`, `changelogpath`, and `appname`, which are used as follows:

* `feed`   
  Is the name of the feed as it will appear on your server, it is 
  the last path component of the URL.
* `feedpath`  
  The actual feed that is served up. This should be a specially prepared xml
  file, including one items which instead of a changelog has a special marker
  telling the sparkleserver where the generated changelog should be inserted.
  See the example feed in `examples/cumulative/testapp.xml` for an example.
* `changelogpath`   
  The path in the file system where the sparkleserver can find changes for each
  version of the program. These files must be have the format
  `version_*.markdown` where * is replaced with the actual version number 
  of the changelog entry.
* `appname`   
  Is used to identify the app in the HTTP user agent string. The app name 
  and version is sent by sparkle in the format `APPNAME/VERSION`.

### The feedfile

The feed used in the cumulative mode is mostly like any other feed, except that
it should contain only one item, the current version. Instead of a description,
the magic string `$changes` should be used as a marker where the actual
changelog will be inserted. It is also possible to include a stylesheet to
format the changelog. This is done by inserting a `<style>` block into the
description. The sparkleserver can read in arbitrary files by using the magic
`$include(filename)`, which can be used to read a stylesheet from a separate
file, e.g.:

    <style>
      $include(changelog.css)
    </style>

See the example feed in `examples/cummulative`.

### Individual changelog entries

The individual changelog entries must currently be formatted using markdown and
their names must conform to the naming scheme shown above. You are free to
format the individual entries as you see fit, currently within the constraints
of markdown.

## Using the webservice

Simply set the `SUFeedURL` to the location where you have started the
sparkleserver instance. If you wish to gather information about your users
systems, be sure to enable `SUEnableSystemProfiling` and enable logging of the
data in a format that suits your needs.

[wsgi]:        http://wsgi.org/wsgi/
[mod_wsgi]:    http://code.google.com/p/modwsgi/
[wsgisimple]:  http://docs.python.org/library/wsgiref.html#module-wsgiref.simple_server
