#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This defines the cfg node object that will be used later, it stores attributes of the model.
"""
import copy
import yaml
from ast import literal_eval

__all__ = ['yaml_to_NODE', 'get_cfg']

VALID_TYPES = {tuple, list, str, int, float, bool, type(None)}

class NODE(dict):
    
    IMMUTABLE = "__immutable__"
    NEW_ALLOWED = "__new_allowed__"
    YAML_LOAD = "__yaml_load__"
    
    def __init__(self, init_dict = {}, key_list = [], new_allowed=True): 
        if init_dict:
            init_dict = self.create_config_tree_from_dict(init_dict, key_list)
        super(NODE, self).__init__(init_dict)
        self.__dict__[NODE.IMMUTABLE] = False
        self.__dict__[NODE.NEW_ALLOWED] = new_allowed
        
    def is_frozen(self):
        return self.__dict__[NODE.IMMUTABLE]

    def is_new_allowed(self):
        return self.__dict__[NODE.NEW_ALLOWED]
    
    def __setattr__(self, name, value):
        if self.is_frozen():
            raise ValueError("Attempted to modify a frozen configuration node: {} to {}".format(name, value))
        self[name] = value

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError(name)
        
    def __str__(self):
        def indent(s_, num_spaces):
            s = s_.split("\n")
            if len(s) == 1:
                return s_
            first = s.pop(0)
            s = [(num_spaces * " ") + line for line in s]
            s = "\n".join(s)
            s = first + "\n" + s
            return s

        r = ""
        s = []
        for k, v in sorted(self.items()):
            seperator = "\n" if isinstance(v, NODE) else " "
            attr_str = "{}:{}{}".format(str(k), seperator, str(v))
            attr_str = indent(attr_str, 2)
            s.append(attr_str)
        r += "\n".join(s)
        return r
    
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, super(NODE, self).__repr__())
    
    def clone(self):
        return copy.deepcopy(self)

    def merge_cfgs(self, yaml_tree):
        merge_ab(yaml_tree, self, self, [])

    @classmethod   
    def create_config_tree_from_dict(cls, dic_og, key_list):
        dic = copy.deepcopy(dic_og)
        for k, v in dic.items():
            if isinstance(v, dict):
                dic[k] = cls(v)
            else:
                assert valid_type(v, allow_cfg_node=False) is True, "Key is not a valid type."
        return dic  
    
    @classmethod
    def decode_value(cls, value):
        if isinstance(value, dict):
            return cls(value)
        if not isinstance(value, str):
            return value
        try:
            value = literal_eval(value)
        except ValueError:
            pass
        except SyntaxError:
            pass
        return value


def get_cfg():
    from .default import _C
    return _C.clone()


def yaml_to_NODE(path):
    with open(path, 'r') as f:
        cfg = yaml.safe_load(f)
    cfg = NODE(cfg)
    return cfg 

        
def valid_type(value, allow_cfg_node=False):
    return (type(value) in VALID_TYPES) or (allow_cfg_node and isinstance(value, NODE)) 
  

def merge_ab(a, b, root, key_list):    
    assert isinstance(a, NODE), "The first argument is not a NODE object."
    assert isinstance(b, NODE), "The second argument is not a NODE object."

    for key, val in a.items():
        full = ".".join(key_list + [key])

        v = copy.deepcopy(val)
        v = b.decode_value(v)

        if key in b:
            o_type = type(v)
            r_type = type(b[key])
            none_type = type(None)
            
            if o_type != r_type:
                condition_1 = (r_type == none_type and o_type in VALID_TYPES)
                condition_2 = (o_type == none_type and r_type in VALID_TYPES)
                if not condition_1:
                    if not condition_2:
                        raise ValueError("Wrong types, {} to {} for {}, {}: {}.".format(o_type, r_type, v, b[key], full))
                        
            if isinstance(v, NODE):
                try:
                    merge_ab(v, b[key], root, key_list + [key])
                except BaseException:
                    raise RuntimeError("Recursive merging of .yaml files failed.")
            else:
                b[key] = v
        elif b.is_new_allowed():
            b[key] = v
        else:
            raise KeyError("Non-existent config key: {}".format(full))
                       

    
    