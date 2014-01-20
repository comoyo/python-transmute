# python-transmute

Automatically update Python Eggs on application startup -- or, you know,
whenever, really.

## Overview

The idea behind this module is to support self-updating Python applications:
probing remote repositories for updated components, fetching updates and making
them available for use. Components are assumed to be standard Python Eggs.
Repositories are then containers for these eggs.

Under the hood, `setuptools` is used to parse and fulfill requirements, based
on listings of available eggs obtained from each repository. The application is
re-launched through execve with an adjusted environment to pick up updated
packages.

The application writer controls the packages to update, repositories each
package is grabbed from, and where in the code an update is actioned.

## Example

This is a script that requests the 'hello' package to be updated from the
`dist` folder in the current working directory:

```python
    import transmute

    transmute.require([ 'hello' ], sources=[ 'dist' ])
    transmute.update()

    import hello
    hello.greet('world')
```

## Open issues

Update failures, a missing network connection and broken packages shouldn't
prevent a previously running command from proceeding. In practice, some more
hardening is needed.

No effort is spent trying to verify packages or checking package signatures.
This would be a nice addition.

Currently, the only type of "remote" repository supported is a directory in the
local filesystem :-)
