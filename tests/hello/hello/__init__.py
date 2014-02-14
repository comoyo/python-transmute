import pkg_resources

try: version = pkg_resources.require(__name__)[0].version
except: version = 'unknown'

def greet(name='World'):
    print "Hi, %s! -- from version %s of %s" % (name, version, __name__)
