from pymongo import MongoClient
from regearbot_package.config import MONGO_CLIENT


class MongoDataManager:
    def __init__(self):
        self.client = MongoClient(MONGO_CLIENT.get('client'))
        self.db = self.client.get_database(MONGO_CLIENT.get('db'))
        self.collection = self.db.get_collection(MONGO_CLIENT.get('collection'))

    def upload_objects_to_db(self, victim_object: dict) -> bool:
        # checks EventId, if no object with the same EventId -> Upload
        event_id = victim_object.get('EventId')
        query = self.collection.find_one({"EventId": event_id})

        if query:
            return False
        else:
            self.collection.insert_one(victim_object)
            return True

    def request_objects_to_regear(self) -> list:
        # get all objects where is_regeared = False
        query = {"is_regeared": False}
        cursor = self.collection.find(query)
        docs = list(cursor).copy()
        return docs

    def update_none_regeared_objects_to_regeared(self):
        query = {"is_regeared": False}
        new_values = {"$set": {"is_regeared": True}}
        self.collection.update_many(query, new_values)

    def get_quantity_of_objects_by_regear(self, is_regeared: bool) -> int:
        query = {"is_regeared": is_regeared}
        return self.collection.count_documents(query)

    # ----------------- MANAGEMENT DEBUG METHODS -------------------

    def debug_delete_objects_from_db(self, my_query: dict):
        query = self.collection.delete_one(my_query)
        print(query.deleted_count)

    def debug_delete_multiple_objects_from_db(self):
        query = self.collection.delete_many({})
        print(query.deleted_count, " jsons deleted.")

    def debug_search_object_by_event_id(self, event_id: int) -> bool:
        query = self.collection.find_one({"EventId": event_id})
        return True if query else False

    def debug_set_objects_to_not_regeared(self):
        query = {"is_regeared": True}
        new_values = {"$set": {"is_regeared": False}}
        self.collection.update_many(query, new_values)


class MongoZvzBuildsManager:
    def __init__(self):
        self.client = MongoClient(MONGO_CLIENT.get('client'))
        self.db = self.client.get_database(MONGO_CLIENT.get('db'))
        self.collection = self.db.get_collection(MONGO_CLIENT.get('builds_collection'))

    def upload_zvz_builds(self, builds: list[dict]) -> dict:
        try:
            self.collection.insert_many(builds)
        except Exception as e:
            return {"status": False, "message": "an error occurred while uploading data", "error": {e}}
        else:
            return {"status": True, "message": "data uploaded successfully"}

    def clear_zvz_builds(self):
        try:
            response = self.collection.delete_many({})
        except Exception as e:
            return {"status": False, "message": "an error occurred while uploading data", "error": {e}}
        else:
            return {"status": True, "message": "builds collection wiped successfully", "count": {response.deleted_count}}

