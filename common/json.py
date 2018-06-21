from __future__ import absolute_import

from disco.types.base import Model
from datetime import datetime
import json


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Model):
            return o.to_dict()

        return json.JSONEncoder.default(self, o)


def json_dumps(*args, **kwargs):
    kwargs['cls'] = JSONEncoder
    return json.dumps(*args, **kwargs)
