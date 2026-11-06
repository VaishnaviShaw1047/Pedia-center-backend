from pymongo import MongoClient
# import the MongoClient class from the pymongo library, 
# which is used to connect to a MongoDB server and interact with the database.


MONGO_URL = "mongodb://localhost:27017"
# connect to the MongoDB server running on localhost at port 27017. 
# This is the default URL for a local MongoDB instance.

client = MongoClient(MONGO_URL)
# create a client instance of MongoClient and connect to the MongoDB server using the provided URL. 
# This allows us to interact with the database.

# use mongoclient to establish connection btw mongodb and fastapi
db = client["pedia_centre"]
# access my database named "pedia_centre" from the MongoDB server.


users_collection = db["users"]
guardians_collection = db["guardians"]
patients_collection = db["patients"]
doctors_collection = db["doctors"]
appointments_collection = db["appointments"]
treatment_records_collection = db["treatment_records"]
doctor_assignments_collection = db["doctor_assignments"]
# create collection objects for each of the collections in the "pedia_centre" database.
