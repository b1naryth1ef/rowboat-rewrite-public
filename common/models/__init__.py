from peewee import Model
from playhouse.db_url import connect

db = connect('postgresext://rowboat@localhost:5444/rowboat?register_hstore=false&autorollback=true')

class BaseModel(Model):
    class Meta:
        database = db
