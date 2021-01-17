import uuid

url = 'https://gs.sit.edu.cn/'
print(type(uuid.uuid5(uuid.NAMESPACE_URL, url)))
