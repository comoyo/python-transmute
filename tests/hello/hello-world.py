import transmute

transmute.require([ 'hello' ], sources=[ 'dist' ])
transmute.update()

import hello
hello.greet()
