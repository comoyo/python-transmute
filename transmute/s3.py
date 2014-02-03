#   Copyright 2014 Telenor Digital AS
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may not
#   use this file except in compliance with the License. You may obtain a copy
#   of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import base64
import email.utils
import hashlib
import hmac
import json
import os
import urllib
import urllib2
import xml.etree.ElementTree

from transmute.basket import Basket, register_basket_factory
from transmute.bootstrap import _download


def _get_s3_endpoint():
    region = os.environ.get('AWS_DEFAULT_REGION') \
            or os.environ.get('EC2_REGION')
    if not region \
            or region == 'us-east-1':
        return 'https://s3.amazonaws.com'
    if region == 'EU':
        region = 'eu-west-1'
    return 'https://s3-%s.amazonaws.com' % region

def _get_aws_credentials():
    for provider in [
                _aws_credentials_from_file,
                _aws_credentials_from_environment,
                _aws_credentials_from_metadata,
            ]:
        try: return provider()
        except: pass

    return None, None, None

def _aws_credentials_from_file():
    config = {}
    with open(os.environ['AWS_CREDENTIAL_FILE']) as credential_file:
        for line in credential_file:
            name, sep, value = line.partition('=')
            if sep:
                config[name.strip()] = value.strip()
    return config['AWSAccessKeyId'], config['AWSSecretKey'], None

def _aws_credentials_from_environment():
    return os.environ['AWS_ACCESS_KEY'], os.environ['AWS_SECRET_KEY'], \
            os.environ.get('AWS_SECURITY_TOKEN', None)

def _aws_credentials_from_metadata():
    url = 'http://169.254.169.254/latest/meta-data/iam/security-credentials'
    role = urllib2.urlopen(url, timeout=1).read()
    credentials = json.load(urllib2.urlopen(url + '/' + role, timeout=1))
    return credentials['AccessKeyId'], credentials['SecretAccessKey'], \
            credentials['Token']


class _S3BucketFolder:
    """A read-only, view over a flat directory in AWS S3."""

    endpoint = _get_s3_endpoint()
    access_key, secret_key, security_token = _get_aws_credentials()

    def __init__(self, bucket, prefix=''):
        self.bucket = bucket
        self.prefix = prefix + '/'

    def _request(self, path, query=None):
        headers = { 'Host': self.bucket }
        self._authenticate_request(path, headers)
        url = self.endpoint + path + (query or '')

        request = urllib2.Request(url, headers=headers)
        response = urllib2.urlopen(request)
        if response.getcode() == 200:
            return response

        raise RuntimeError('%s: %s' % (response.getcode(), response.read()))

    def _xml_request(self, path, query=None):
        return xml.etree.ElementTree.parse(self._request(path, query))

    def _authenticate_request(self, path, headers):
        # See http://docs.aws.amazon.com/AmazonS3/latest/dev/RESTAuthentication.html
        # Shortcuts taken liberally, this is not a full implementation.

        if not self.access_key:
            return

        date = email.utils.formatdate()
        headers['Date'] = date

        message = 'GET\n\n\n' + date + '\n'
        if self.security_token:
            headers['x-amz-security-token'] = self.security_token
            message += 'x-amz-security-token:' + self.security_token + '\n'
        message += '/' + self.bucket + path

        h = hmac.new(self.secret_key, message, hashlib.sha1)
        signature = base64.b64encode(h.digest())

        headers['Authorization'] = 'AWS %s:%s' % (self.access_key, signature)

    def get_bucket_location(self):
        return self._xml_request('/?location').getroot().text

    def list_objects(self):
        """List objects in directory.

        Sub-directories are not listed or traversed. Entries don't contain the
        common S3 key prefix.
        """
        marker = ''
        query = '?delimiter=/&encoding-type=url&prefix=' \
                + urllib.quote_plus(self.prefix, '/')

        while True:
            result = self._xml_request('/', query=query + marker)
            for key in result.iterfind(
                    '{http://s3.amazonaws.com/doc/2006-03-01/}Contents/'
                    '{http://s3.amazonaws.com/doc/2006-03-01/}Key'):

                key = urllib.unquote_plus(key.text)
                yield key[len(self.prefix):]

            marker = result.find(
                    '{http://s3.amazonaws.com/doc/2006-03-01/}NextMarker')
            if marker is None:
                break
            marker = '&marker=' + marker.text

    def get_object(self, name):
        """Read object from S3.

        Returns a tuple consisting of the MD5 hash of the content and a
        file-like stream for it.
        """
        path = urllib.quote_plus('/' + self.prefix + name, '/')
        response = self._request(path)

        return response.headers['ETag'][1:-1], response


class S3Basket(Basket):
    def initialize(self):
        assert self.url.startswith('s3://')

        bucket, _, prefix = self.url[5:].partition('/')
        self.s3_bucket = _S3BucketFolder(bucket, prefix)

        for filename in self.s3_bucket.list_objects():
            self.add_package(filename, filename=filename)

    def fetch(self, dist, metadata):
        md5sum, data = self.s3_bucket.get_object(metadata['filename'])
        _download(data, dist.location, md5sum)


register_basket_factory('s3', S3Basket)
