import sys
import transmute

transmute.require([ 'hello' ], sources=[ '../../hello/dist' ])
transmute.update()

import hello
hello.greet('test')
