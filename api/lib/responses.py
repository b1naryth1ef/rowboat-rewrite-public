from flask import Response
import json


class APIResponse(Response):
    def __init__(self, obj=None, code=200):
        super(APIResponse, self).__init__()

        if obj:
            if hasattr(obj, 'to_dict'):
                obj = obj.to_dict()

            self.data = json.dumps(obj)
            self.status_code = code
        else:
            self.status_code = 204
            self.data = ''

        self.mimetype = 'application/json'


class APIError(Exception):
    def __init__(self, message, code=400):
        self.response = APIResponse({
            'error': message,
        }, code=code)
