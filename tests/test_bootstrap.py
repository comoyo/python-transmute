from nose.tools import *
import os
import os.path
import shutil
import sys
import subprocess
import tempfile

_home = None
_base_dir = os.path.dirname(__file__)

def setUp():
    global _home
    _home = tempfile.mkdtemp()
    
    hello_dir = os.path.join(_base_dir, 'hello')
    subprocess.check_call([ sys.executable, 'setup.py', 'bdist_egg' ], cwd=hello_dir)

def tearDown():
    global _home
    shutil.rmtree(_home)
    _home = None

def test_generator():
    test_dir = os.path.join(_base_dir, 'bootstrap-tests')
    for entry in os.listdir(test_dir):
        path = os.path.join(test_dir, entry)
        if os.path.isdir(path):
            yield check_main, path

def check_main(path):
    cwd = path

    main_py = os.path.join(path, 'main.py')
    try:
        with open(os.path.join(path, 'output')) as output_file:
            expected_output = output_file.read()
    except:
        expected_output = ''

    env = os.environ.copy()
    env['HOME'] = _home

    output = subprocess.check_output([ sys.executable, main_py ], cwd=cwd,
            env=env, stderr=subprocess.STDOUT)
    
    assert_equals(expected_output, output)
