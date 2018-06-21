from __future__ import absolute_import

from datetime import datetime
from msgpack import packb, unpackb


def encode_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def pack(obj):
    return packb(obj, default=encode_datetime, use_bin_type=True)


def unpack(obj):
    return unpackb(obj)
