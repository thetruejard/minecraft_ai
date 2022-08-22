
import pydoc


def get_full_qualified_name(obj: object):
    return obj.__module__ + '.' + obj.__qualname__

def get_obj_from_qualified_name(name: str):
    return pydoc.locate(name)


def serialize_function(func: callable):
    return get_full_qualified_name(func)

def deserialize_function(serialized: str):
    return get_obj_from_qualified_name(serialized)


def serialized_class(klass: type):
    return get_full_qualified_name(klass)

def deserialize_class(serialized: str):
    return get_obj_from_qualified_name(serialized)
