from pymongo import MongoClient
from regearbot_package.config import MONGO_CLIENT


class MongoDataManager:
    def __init__(self, database="albion", database_collection="regearbot"):
        self.client = MongoClient(MONGO_CLIENT)
        self.db = self.client.get_database(database)
        self.collection = self.db.get_collection(database_collection)

    def upload_objects_to_db(self, victim_object: dict) -> bool:
        # checks EventId, if no object with the same EventId -> Upload
        event_id = victim_object.get('EventId')
        query = self.collection.find_one({"EventId": event_id})

        if query:
            return False
        else:
            self.collection.insert_one(victim_object)
            return True

    def export_objects_to_csv(self):

        # STEP[1] get all objects where is_regeared = False
        query = {"is_regeared": False}
        cursor = self.collection.find(query)
        docs = list(cursor).copy()

        # STEP[2] convert all exported objects to is_regeared = True
        new_values = {"$set": {"is_regeared": True}}
        self.collection.update_many(query, new_values)

        # TODO: export to excel instead of return docs object
        return docs

    # ----------------- MANAGEMENT DEBUG METHODS -------------------

    def delete_objects_from_db(self):
        my_query = {"category": ""}
        query = self.collection.delete_one(my_query)
        print(query.deleted_count)

    def delete_multiple_objects_from_db(self):
        my_query = {"category": "Victim_to_regear"}
        query = self.collection.delete_many(my_query)
        print(query.deleted_count, " jsons deleted.")

    def get_quantity_of_objects_in_collection(self):
        query = self.collection.count_documents({"category": "Victim_to_regear"})
        print(query)

    def search_object_by_event_id(self, event_id: int) -> bool:
        query = self.collection.find_one({"EventId": event_id})
        return True if query else False


