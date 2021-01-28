
class Database():
    def __init__(self, user, passwd, db):


def get_database():
    mongo_user, mongo_pass, mongo_db = \
        settings.get("mongo_username"), settings.get("mongo_password"), settings.get("mongo_db")
    client = MongoClient('mongodb+srv://' + mongo_user + ":" + mongo_pass + "@cluster0.n0rcn.mongodb.net/")
    return client.get_database(mongo_db)