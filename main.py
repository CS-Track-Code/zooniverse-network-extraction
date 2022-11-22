import export
from pymongo import MongoClient

# Define the localhost and port of the MongoDB
localhost = '127.0.0.1'
port = '27017'
collection_name = "zooniverse"

# Define dict for relevant project ids
project_ids = {
    '5733': 'Galaxy Zoo',
    '1104': 'Gravity Spy',
    '478': 'Seabirdwatch',
    '2439': 'Snapshot Wisconsin',
    '2789': 'Wildwatch Kenya',
    '3393': 'Galaxy Nurseries',
    '6263': 'Penguin Watch'
}

delims = {
    'q1': {'start_m': 1,
           'start_d': 1,
           'end_m': 3,
           'end_d': 31},
    'q2': {'start_m': 4,
           'start_d': 1,
           'end_m': 6,
           'end_d': 30},
    'q3': {'start_m': 7,
           'start_d': 1,
           'end_m': 9,
           'end_d': 30},
    'q4': {'start_m': 10,
           'start_d': 1,
           'end_m': 12,
           'end_d': 31},

}

# connect to MongoDB
client = MongoClient(localhost+":"+port)
db = client[collection_name]

# Run necessary functions
export.exportAnnotations('filepath for annotations file')
export.exportUserTrajectories(db, 2016, 2022, project_ids, delims)
export.exportNetworkDataTotal(db, project_ids, 'joint')
export.exportComments(db,project_ids)
export.exportRoleChanges(db, project_ids)