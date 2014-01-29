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

import botocore.session
import contextlib
from transmute.basket import Basket, register_basket_factory
from transmute.bootstrap import _download

class S3Error(Exception):
    def __init__(self, response, data):
        Exception.__init__(self, "%s: %s" % (response, data))

class _S3Bucket:

    bucket_regions = {}

    def __init__(self, bucket, prefix):
        self.session = botocore.session.get_session()
        self.s3 = self.session.get_service('s3')

        self.bucket = bucket
        self.prefix = prefix

        self._fill_endpoint()

    @staticmethod
    def _get_data(result):
        response, data = result
        if response.status_code != 200:
            raise S3Error(response, data)
        return data

    def _s3_call(self, operation, **kwargs):
        operation = self.s3.get_operation(operation)
        return self._get_data(operation.call(self.endpoint, **kwargs))

    def _s3_paginate(self, operation, **kwargs):
        operation = self.s3.get_operation(operation)
        for result in operation.paginate(self.endpoint, **kwargs):
            yield self._get_data(result)

    def _fill_endpoint(self):
        region = None
        try:
            region = self.bucket_regions[self.bucket]
        except KeyError:
            self.endpoint = self.s3.get_endpoint(None)

            result = self._s3_call('GetBucketLocation', bucket=self.bucket)
            self.bucket_regions[self.bucket] = \
                    region = result['LocationConstraint']

        self.endpoint = self.s3.get_endpoint(region)

    def list_objects(self):
        prefix_len = len(self.prefix)
        for results in self._s3_paginate('ListObjects', delimiter='/',
                bucket=self.bucket, prefix=self.prefix):
            # A single flat directory is exposed, entries falling under
            # results['CommonPrefixes'] are ignored altogether.
            for obj in results['Contents']:
                yield obj['Key'][prefix_len:]

    def get_object(self, name):
        result = self._s3_call('GetObject', bucket=self.bucket,
                key=self.prefix + name)
        return result['ETag'], result['Body']


class S3Basket(Basket):
    def initialize(self):
        assert self.url.startswith('s3://')

        bucket, _, prefix = self.url[5:].partition('/')
        self.s3_bucket = _S3Bucket(bucket, prefix + '/')

        for filename in self.s3_bucket.list_objects():
            self.add_egg(filename, filename=filename)

    def fetch(self, dist, **metadata):
        md5sum, data = self.s3_bucket.get_object(metadata['filename'])

        if not hasattr(data, 'close'):
            data.close = lambda: None

        _download(data, dist.location, md5sum[1:-1])


register_basket_factory('s3', S3Basket)
