
import pydoc


def get_full_qualified_name(obj: object) -> str:
    return obj.__module__ + '.' + obj.__qualname__

def get_obj_from_qualified_name(name: str) -> type:
    return pydoc.locate(name)


def serialize_class(klass: type) -> str:
    return get_full_qualified_name(klass)

def deserialize_class(serialized: str) -> type:
    return get_obj_from_qualified_name(serialized)
