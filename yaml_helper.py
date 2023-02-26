from os import makedirs, path
from yaml import load , dump
try:
    from yaml import CSafeLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import SafeLoader as Loader, Dumper

def load_yaml(filepath):
    with open(filepath) as stream:
        return load(stream, Loader=Loader)

def dump_yaml(data, filepath):
    makedirs(path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as stream:
        dump(data, stream, Dumper=Dumper, default_flow_style=False)
