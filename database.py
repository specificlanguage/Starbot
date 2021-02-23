from pymongo import MongoClient
import helpers

class Database():
    def __init__(self):
        credentials = helpers.get_credentials()
        self.client = MongoClient('mongodb+srv://' + credentials[0] + ":" +
                                  credentials[1] + "@cluster0.n0rcn.mongodb.net/")
        self.database = self.client[credentials[2]]

    def num_found(self, collection, criteria):
        return self.database[collection].count_documents(criteria)