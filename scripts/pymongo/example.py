from pymongo import MongoClient

uri = "mongodb://<username>:<password>@localhost:27017/"
client = MongoClient(uri)

try:
    database = client.get_database("focusbuddy")
    movies = database.get_collection("block_list")

    query = {"domain": "https://facebook.com"}
    blocked_site = movies.find_one(query)

    print(blocked_site)

    client.close()

except Exception as e:
    raise Exception("Unable to find the document due to the following error: ", e)
