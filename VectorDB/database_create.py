import json
import cassio
with open("keys.json", "r") as file:
    data = json.load(file)
ASTRA_DB_APPLICATION_TOKEN=data['ASTRA_DB_APPLICATION_TOKEN']
ASTRA_DB_ID=data['ASTRA_DB_ID']
cassio.init(token=ASTRA_DB_APPLICATION_TOKEN,database_id=ASTRA_DB_ID)