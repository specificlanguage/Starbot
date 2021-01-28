from pymongo import MongoClient
import settings

class Database():
    def __init__(self):
        credentials = settings.get_credentials()
        self.client = MongoClient('mongodb+srv://' + credentials[0] + ":" +
                                  credentials[1] + "@cluster0.n0rcn.mongodb.net/")
        self.database = self.client[credentials[2]]