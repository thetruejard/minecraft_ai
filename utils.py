
import itertools
import pydoc
from typing import Iterable

import torch


def get_full_qualified_name(obj: object) -> str:
    return obj.__module__ + '.' + obj.__qualname__

def get_obj_from_qualified_name(name: str) -> type:
    return pydoc.locate(name)


def serialize_class(klass: type) -> str:
    return get_full_qualified_name(klass)

def deserialize_class(serialized: str) -> type:
    return get_obj_from_qualified_name(serialized)



def name_generator(base_name: str):
    yield base_name
    i = 0
    while True:
        yield base_name + '_' + str(i)
        i += 1

def create_new_name(base_name: str, existing_objects: Iterable):
    '''Assumes each object in existing_objects has a ".name" attribute'''
    ng = name_generator(base_name)
    name = next(ng)
    while any(e.name == name for e in existing_objects):
        name = next(ng)
    return name

def create_new_id(existing_keys: Iterable):
    return next(itertools.filterfalse(existing_keys.__contains__, itertools.count(1)))


def optimizer_from_name(name: str):
    o = torch.optim
    return {
        'adadelta':     o.Adadelta,
        'adagrad':      o.Adagrad,
        'adam':         o.Adam,
        'adamw':        o.AdamW,
        'sparseadam':   o.SparseAdam,
        'adamax':       o.Adamax,
        'asgd':         o.ASGD,
        'lbfgs':        o.LBFGS,
        'nadam':        o.NAdam,
        'radam':        o.RAdam,
        'rmsprop':      o.RMSprop,
        'rprop':        o.Rprop,
        'sgd':          o.SGD
    }[name.lower()]

def name_from_optimizer(opt: type):
    o = torch.optim
    return {
        o.Adadelta:     'adadelta',
        o.Adagrad:      'adagrad',
        o.Adam:         'adam',
        o.AdamW:        'adamw',
        o.SparseAdam:   'sparseadam',
        o.Adamax:       'adamax',
        o.ASGD:         'asgd',
        o.LBFGS:        'lbfgs',
        o.NAdam:        'nadam',
        o.RAdam:        'radam',
        o.RMSprop:      'rmsprop',
        o.Rprop:        'rprop',
        o.SGD:          'sgd'
    }[opt]
