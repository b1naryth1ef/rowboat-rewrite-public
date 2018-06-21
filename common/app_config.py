import yaml


class RowboatConfig(object):
    @classmethod
    def from_file(cls, path):
        inst = cls()

        with open(path, 'r') as f:
            for k, v in yaml.load(f).iteritems():
                setattr(inst, k, v)
        return inst

    database_shards = {}
