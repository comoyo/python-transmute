import pkg_resources

version = pkg_resources.require(__name__)[0].version

def greet(name='World'):
    print "Hi, %s! -- from version %s of %s" % (name, version, __name__)
