import sys
import os
import os.path
import re
import csv
import sqlite3
import wsgiref.util
try:
    # Lives here in 2.5
    from urlparse import parse_qs
except ImportError:
    # But here in 2.6
    from cgi import parse_qs
from datetime import datetime
from BaseHTTPServer import BaseHTTPRequestHandler

block_size = 1024
valid_path = re.compile('/[a-zA-Z0-9$-_\.+!\*\'(),]*\.xml')

data_keys = ['appName', 'appVersion', 'cpuFreqMHz', 'cpu64bit',
        'cpusubtype', 'cputype', 'lang', 'model', 'ncpu',
        'osVersion', 'ramMB']

apache_combined = '%h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-agent}i"'
apache_common   = '%h %l %u %t "%r" %>s %b'
angle_brackets  = re.compile('%[<>]([a-zA-Z])')

csv_data_keys     = ['sp.time', 'sp.feed', 'sp.ip'] + data_keys
sqlite_data_keys  = ['sp.time', 'sp.feed', 'sp.ip'] + data_keys


class SparkleServerException(Exception): pass

def get_env(thing, environ, fallback=None):
    otherthing = thing.replace('.', '_')
    return environ.get(thing, environ.get(otherthing, fallback))

def get_env_required(key, e):
    value = get_env(key, e)
    if value == None:
        raise SparkleServerException('Please specify "%s"' % key)
    return value


def log_apache(data, e):
    req_date = get_env('sparkleserver.data.request_date', e, datetime.now())

    format = get_env('sparkleserver.log.apache.format', e, apache_combined)
    if format == 'combined':
        log_format = apache_combined
    elif format == 'common':
        log_format = apache_common
    else:
        log_format = format

    # See:
    # http://httpd.apache.org/docs/2.2/mod/mod_log_config.html
    # http://httpd.apache.org/docs/2.2/logs.html
    parameters = {
            '%': '%',
            'a': e.get('REMOTE_ADDR', '-'),
            'A': e.get('HTTP_HOST', '-'),
            'B': str(get_env('sparkleserver.data.response_size', e, 0)),
            'b': str(get_env('sparkleserver.data.response_size', e, '-')),
            # %{Foobar}C
            #'%D': '-',
            # %{FOOBAR}e
            'e': lambda x: e.get(x, '-'),
            'f': e.get('PATH_INFO', '-'),
            'h': e.get('REMOTE_ADDR', '-'),
            'H': e.get('wsgi.url_scheme', '-'),
            # %{Foobar}i
            'i': lambda x: e.get('HTTP_' + x.upper().replace('-', '_'), '-'),
            #'%k': '-',
            'l': '-',
            'm': e.get('REQUEST_METHOD', '-'),
            # %{Foobar}n
            # %{Foobar}o
            # %p
            # %{format}p
            'P': os.getpid(),
            # %{format}P
            'q': e.get('QUERY_STRING', ''),
            'r': '%s %s%s%s %s' % (
                e.get('REQUEST_METHOD', ''),
                e.get('PATH_INFO', ''),
                (e.get('QUERY_STRING', '') and '?' or ''),
                e.get('QUERY_STRING', ''),
                e.get('SERVER_PROTOCOL', '')),
            's': '200',
            't': req_date.strftime('[%d/%m/%Y:%H:%M:%S') +\
                    (req_date.strftime('%z') and ' ' or '') + \
                    req_date.strftime('%z]'),
            # %{format}t
            #'%T': '-',
            'u': e.get('REMOTE_USER', '-'),
            'U': e.get('PATH_INFO', '-'),
            #'%v': '-',
            #'%V': '-',
            # %O
            # %I
            }
    log_format = angle_brackets.sub(r'%\1', log_format)
    log_line = ""
    while log_format:
        if log_format[0] == '%':
            if log_format[1] == '{':
                log_format = log_format[2:]
                key = ""
                while log_format and log_format[0] != '}':
                    key += log_format[0]
                    log_format = log_format[1:]
                fn = parameters.get(log_format[1], None)
                if fn and callable(fn):
                    log_line += fn(key)
                else:
                    log_line += '%%{%s}%s' % (key, log_format[1])
                log_format = log_format[1:]
            else:
                log_line += parameters.get(log_format[1], '%' + log_format[1])
                log_format = log_format[1:]
        else:
            log_line += log_format[0]
        log_format = log_format[1:]
    filename = get_env_required('sparkleserver.log.apache.path', e)

    fp = open(filename, 'a')
    fp.write(log_line + '\n')
    fp.close()

def data2row(data, e, cols):
    row = []
    data_available = 0
    for key in cols:
        if key == 'sp.time':
            row.append(e.get('sparkleserver.data.request_date', datetime.now()))
        elif key == 'sp.ip':
            row.append(e.get('REMOTE_ADDR', None))
        elif key == 'sp.feed':
            path = e.get('PATH_INFO')
            row.append(path[1:][:-4])
        elif key == 'sp.feedpath':
            path = e.get('PATH_INFO')
            row.append(path)
        else:
            d = data.get(key, None)
            data_available = data_available or d != None
            row.append(data.get(key, None))
    return (row, data_available)

def get_cols(col_key, extra_key, default_cols, e):
    # FIXME: check for validity of sp.columns
    columns = get_env(col_key, e)
    if columns:
        keys = [f.strip() for f in columns.split(',')]
    else:
        keys = default_cols
    extra_columns = get_env(extra_key, e)
    if extra_columns:
        keys += [f.strip() for f in extra_columns.split(',')]
    return keys

def log_csv(data, e):
    filename = get_env_required('sparkleserver.log.csv.path', e)

    kwargs = dict()
    quoting = get_env('sparkleserver.log.csv.quoting', e)
    if quoting:
        quoting = getattr(csv, 'QUOTE_' + quoting, None)
        if not quoting:
            raise SparkleServerException(
                    'unknown value in "sparkleserver.log.csv.quoting"')
        kwargs['quoting'] = quoting
    quotechar = get_env('sparkleserver.log.csv.quoting', e)
    if quotechar: kwargs['quotechar'] = quotechar
    lineterminator = get_env('sparkleserver.log.csv.lineterminator', e)
    if lineterminator: kwargs['quotechar'] = lineterminator
    escapechar = get_env('sparkleserver.log.csv.escapechar', e)
    if escapechar: kwargs['quotechar'] = escapechar
    delimiter = get_env('sparkleserver.log.csv.delimiter', e)
    if delimiter: kwargs['quotechar'] = delimiter
    doublequote = get_env('sparkleserver.log.csv.doublequote', e)
    if doublequote: 
        kwargs['quotechar'] = (doublequote == '1' or doublequote == 'True')

    keys = get_cols('sparkleserver.log.csv.columns',
                    'sparkleserver.log.csv.extra_columns',
                    csv_data_keys,
                    e)
    (row, data_available) = data2row(data, e, keys)

    if not data_available:
        # No data, don't log anything
        return

    fp = open(filename, 'a')
    w = csv.writer(fp, **kwargs)
    w.writerow(row)
    fp.close()

def log_sqlite(data, e):
    filename = get_env_required('sparkleserver.log.sqlite.path', e)
    table    = get_env('sparkleserver.log.sqlite.table', e, 'sparkle_log')

    keys = get_cols('sparkleserver.log.sqlite.columns',
                    'sparkleserver.log.sqlite.extra_columns',
                    sqlite_data_keys,
                    e)

    col_names              = ','.join(['"%s"' % k for k in keys])
    (cols, data_available) = data2row(data, e, keys)
    cols_s                 = ','.join(['?'] * len(cols))

    if not data_available:
        # No data, don't log anything
        return

    conn = sqlite3.connect(filename)
    c = conn.cursor()
    try:
        c.execute('create table %s (%s)' % (table, col_names))
        conn.commit()
    except sqlite3.OperationalError, e:
        pass
    sql = 'insert into %s (%s) values (%s)' % (table, col_names, cols_s)
    c.execute(sql, cols)
    conn.commit()
    conn.close()

def log_sqlalchemy(data, environ):
    pass
def log_appengine(data, environ):
    pass

def render_404(environ, start_response):
    status = '404 %s' % BaseHTTPRequestHandler.responses[404][0]
    headers = [('Content-type', 'text/plain')]
    start_response(status, headers)

    return ['File not found: %s' % wsgiref.util.request_uri(environ, False)]

def render_500(environ, start_response, msg=None):
    if msg:
        if msg[:-1] != '\n': msg += '\n'
        msg = 'ERROR: ' + msg
        environ['wsgi.errors'].write(msg)
    status = '500 %s' % BaseHTTPRequestHandler.responses[500][0]
    headers = [('Content-type', 'text/plain')]
    start_response(status, headers)

    return [BaseHTTPRequestHandler.responses[500][0]]

def sparkle_server(environ, start_response):
    environ['sparkleserver.data.request_time'] = datetime.now()
    feedpath = get_env('sparkleserver.feedpath', environ, None)
    cumulative = get_env('sparkleserver.cumulative', 
            environ, {})
    if not feedpath and not cumulative:
        return render_500(
                environ, 
                start_response,
                msg='sparkleserver.feedpath or ' +
                'sparkleserver.cumulative not in environment')
    path = environ['PATH_INFO']
    if not valid_path.match(path):
        return render_404(environ, start_response)

    fp = None
    try:
        cumulative_config = cumulative[path[1:]]
    except KeyError:
            pass
    else:
        try:
            fp = open(os.path.join(cumulative_config['feedpath']), 'r')
        except IOError, e:
            return render_500(environ, start_response,
                    msg='cumulative feed not found: ' +
                    cumulative_config['feedpath'])

    if not fp:
        try:
            fp = open(os.path.join(feedpath, path[1:]), 'r')
            environ['sparkleserver.data.response_size'] =\
                    os.fstat(fp.fileno()).st_size
        except IOError, e:
            return render_404(environ, start_response)

    data = parse_qs(environ['QUERY_STRING'])
    # Assume that we never get duplicate keys, ie:
    # ?appName=App.app&appName=App2.app, this ought to be a safe assumption(?)
    for key in data:
        data[key] = data[key][0]

    methods = [('sparkleserver.log.apache.path', 'apache'),
               ('sparkleserver.log.sqlite.path', 'sqlite'),
               ('sparkleserver.log.csv.path', 'csv')]
    log_methods = []
    for method in methods:
        if get_env(method[0], environ, None):
            log_methods.append(method[1])
    try:
        if 'apache' in log_methods:
            log_apache(data, environ)
        if 'csv' in log_methods:
            log_csv(data, environ)
        if 'sqlite' in log_methods:
            log_sqlite(data, environ)
    except SparkleServerException, e:
        return render_500(environ, start_response, str(e))

    status = '200 OK'
    headers = [('Content-type', 'text/xml')]
    start_response(status, headers)

    if cumulative:
        feed = fp.read()
        import re
        import glob
        import markdown2
        regex = \
        re.compile(r'\$include\((?P<inc_file>[^\)]*)\)|(?P<changes>\$changes)')
        def subber(match):
            matches = match.groupdict()
            if matches.get('changes', None):
                r = re.escape(cumulative_config['appname']) + '/([a-zA-Z0-9.]*)'
                r = re.compile(cumulative_config.get('versionregex', r))
                version = r.search(environ['HTTP_USER_AGENT'])
                content = ''
                files = \
                glob.glob(os.path.join(cumulative_config['changelogpath'], 'version_*'))
                # FIXME: Customised filter
                compare = cumulative_config.get('compare', cmp)
                files.sort(cmp=compare, reverse=True)
                if not version:
                    if len(files) >= 1: files = [files[0]]
                else:
                    version = version.group(1)
                    files = [f for f in files if
                            compare(os.path.splitext(os.path.basename(f)[8:])[0],
                        version) == 1]
                content = [open(f).read() for f in files]
                # FIXME: Deal with differnet kinds of content
                content = [markdown2.markdown(c) for c in content]
                content = '\n'.join(content)
                return content.encode('utf-8')
            elif matches.get('inc_file', None):
                f = matches['inc_file']
                inc_fp = open(os.path.join(cumulative_config['changelogpath'], f))
                content = inc_fp.read()
                inc_fp.close()
                return content
            raise RuntimeException('Bad match!')
        feed = regex.sub(subber, feed)
        return iter(feed)
    else:
        if 'wsgi.file_wrapper' in environ:
            return environ['wsgi.file_wrapper'](fp, block_size)
        else:
            return iter(lambda: fp.read(block_size), '')

if __name__ != '__main__':
    application = sparkle_server
else:
    from wsgiref.simple_server import make_server
    from wsgiref.validate import validator
    from wsgiref.simple_server import WSGIRequestHandler

    if len(sys.argv) == 2 and sys.argv[1] == 'reload':
        import paste.reloader as reloader
        reloader.install()
        print 'reloader installed'

    if not get_env('sparkleserver.feedpath', os.environ):
        print 'Please set the environment variable "sparkleserver_feedpath"'
        print 'to point to the applications feedpath'
        sys.exit(1)

    sparkle_server = validator(sparkle_server)

    httpd = make_server('', 8000, sparkle_server)
    print "Serving on port 8000..."

    # Serve until process is killed
    httpd.serve_forever()
