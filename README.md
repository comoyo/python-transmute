# python-transmute

Automatically update Python Eggs on application startup -- or, you know,
whenever, really.


## Overview

The idea behind this module is to support self-updating Python applications,
namely command-line tools. Transmute probes remote repositories for updated
components, fetches updates and adds them to `sys.path`, making them available
for use in the application.

Components are assumed to be standard Python Eggs. Repositories are then
simple containers for these eggs. Currently PyPI and S3 "folders" are supported
as repositories. (Mostly for testing purposes, local directories are also
supported as repositories).

Under the hood, `pkg_resources` (from `setuptools`) is used to parse and fulfill
requirements, based on listings of available eggs obtained from each repository.
Once updated packages are made available, their modules can be imported or the
application can be re-launched with an adjusted environment to pick up updated
modules.

The application writer controls the packages to update, repositories each
package will be grabbed from, and when an update is actioned.

The philosophy has been that an absent or flaky network should not prevent (or
significantly delay) an application from running on top of outdated packages, if
they've been cached locally. That said, there are currently no provisions for
testing and verifying a successful update or rolling back a failed update.


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


## Bootstrapping an application with `bootstrap.py`

The submodule in [`transmute/bootstrap.py`][1] can be used
on its own to bootstrap other Python modules and applications. It is capable of
downloading packages from PyPI. In this way, `transmute` itself can be loaded
and further used to download additional packages.

[1]: https://github.com/comoyo/python-transmute/blob/master/transmute/bootstrap.py

The script provides a bunch of hooks where users can place their code. In
particular, `main()` can be filled in to fetch application specific packages and
actually launch the application. At the point it is called `transmute` has been
added to `sys.path` (after downloading from PyPI, if needed).

```python
    def main():
        import transmute
        import transmute.s3

        transmute.require([ 'foobar' ],
                sources=[ 's3://foobar-repository/eggs/foobar' ])
        transmute.update()

        import foobar.cli
        return foobar.cli.run()
```

It can also be used as a placeholder for a Python module. If the module itself
is available from PyPI, the corresponding package name would be added to the
`requirements` variable. For other use cases, I sense a pull request coming :-)

At the time of this writing, the only non-standard dependency of the script is
the `pkg_resources` module from the `setuptools` package. The assumption here is
that the module is more or less available everywhere. If this turns out to be a
problem in practice, I suppose the script could be simplified to not require it.


## Supported package formats

Currently, only standard Python eggs are supported. I don't mind adding support
for other formats, formats supported natively by Python are preferred.

In that regard, source tarballs look particularly interesting for pure Python
packages, and seem to be more generally available from PyPI. Unpacking and
importing the packages locally could be a way forward.

Python wheels also look interesting and gaining some traction.


## Supported repositories

### Local repositories

Just a directory with eggs in it. This is mostly useful for testing.

```python
    transmute.require([ 'foobar' ], sources=[ '/opt/basket' ])
```

### PyPI

Transmute supports PyPI's [PyPIJSON](https://wiki.python.org/moin/PyPIJSON)
interface.

```python
    transmute.require([ 'foobar' ], sources=[ transmute.PYPI_SOURCE ])
```

### [Amazon Simple Storage Service (S3)](http://aws.amazon.com/s3/)

Packages can be uploaded to a directory in S3.

While technically Amazon's S3 doesn't have the concept of a folder, the slash
(`'/'`) in S3 key names is abused to sustain the illusion of directories.

Credentials can be provided as environment variables. `transmute` recognizes a
few fairly standard variables:

    - AWS_CREDENTIAL_FILE
    - AWS_ACCESS_KEY, AWS_SECRET_KEY, and (optionally) AWS_SECURITY_TOKEN
    - AWS_DEFAULT_REGION and EC2_REGION

When running in an EC2 instance, transmute may also pick credentials from the
IAM role associated with it.

```python
    import transmute.s3
    transmute.require([ 'foobar' ], sources=[ 's3://bucket/key-prefix' ])
```

### Missing a repository format?

I'm missing a pull request. :-)


## Open issues

- Logging is sorely missing. This can be helpful in debugging, but also to keep
  track of updates and possibly tie in to enabling rollbacks.
- Rolling back a b0rked update.
- Provide hooks for verifying an update before activating it.
- We shouldn't use the network on every run of a given command. Keeping track of
  metadata about repository queries would allow us to limit updates to daily or
  weekly schedules.
- Currently MD5 hashes are used to verify integrity of downloaded packages, as
  advertised by repositories. It would be nice to be able to verify package
  signatures.
- Your pet peeve?
