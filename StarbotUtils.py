import yaml

def get_yaml(file, key):
    return yaml.load(file, Loader=yaml.FullLoader).get(key)