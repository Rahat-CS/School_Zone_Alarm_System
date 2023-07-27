
import re
import yaml

def adjust_structure(struct, command_text):
    """Change an element in a nested structure

    In the simplest case top level values are changed by naming them:
    >>> s = {'a': 1, 'b': 2, 'c': 3}
    >>> adjust_structure(s, 'b=555')
    1
    >>> s
    {'a': 1, 'b': 555, 'c': 3}

    Nested values can be referenced by dot notation: 'a.b.c':
    >>> s = {'a': 1, 'b': {'ba': 2, 'bb': 3}}
    >>> adjust_structure(s, 'b.ba=555')
    1
    >>> s
    {'a': 1, 'b': {'ba': 555, 'bb': 3}}

    Wildcards can be used for individual levels:
    >>> s = {'a': 1, 'b': {'ba': 2, 'bb': 3}}
    >>> adjust_structure(s, '*.ba=555')
    1
    >>> s
    {'a': 1, 'b': {'ba': 555, 'bb': 3}}

    Wildcards can match multiple values (here two):
    >>> s = {'a': {'ba': 2, 'bb': 3}, 'b': {'ba': 2, 'bb': 3}}
    >>> adjust_structure(s, '*.ba=555')
    2
    >>> s
    {'a': {'ba': 555, 'bb': 3}, 'b': {'ba': 555, 'bb': 3}}

    The '**' wildcard can represent multiple levels, so '**.x' would match every
    element named 'x' regardless of where it is in the hierarcy:
    >>> s = {'a': {'aa': {'aaa': 1}}}
    >>> adjust_structure(s, '**.aaa=555')
    1
    >>> s
    {'a': {'aa': {'aaa': 555}}}

    If an element doesn't exist then no change is made:
    >>> s = {'a': 1, 'b': 2, 'c': 3}
    >>> adjust_structure(s, 'd=4')
    0
    >>> s
    {'a': 1, 'b': 2, 'c': 3}

    New values can be any valid YAML (and therefore JSON) encoding:
    >>> s = {'a': 1, 'b': 2, 'c': 3}
    >>> adjust_structure(s, 'b={"d": 32}')
    1
    >>> s
    {'a': 1, 'b': {'d': 32}, 'c': 3}

    List elements can be accessed using the corresponding index:
    >>> s = {'a': [0, 10, 20], 'b': 2, 'c': 3}
    >>> adjust_structure(s, 'a.1=11')
    1
    >>> s
    {'a': [0, 11, 20], 'b': 2, 'c': 3}

    """
    changes = [0]

    def change(struct, key_path, new_value, wildcard=False):
        key = key_path[0]
        if wildcard:
            at_end = len(key_path) == 1
        else:
            key_path = key_path[1:]
            at_end = len(key_path) == 0
        if key == "**":
            change(struct, key_path, new_value, wildcard=True)
            return

        if type(struct) is dict:
            if key == "*":
                for value in struct.values():
                    if type(value) in [dict, list]:
                        change(value, key_path, new_value)
            elif key in struct:
                if at_end:
                    struct[key] = new_value
                    changes[0] += 1
                else:
                    change(struct[key], key_path, new_value)
            elif wildcard:
                for value in struct.values():
                    if type(value) in [dict, list]:
                        change(value, key_path, new_value, wildcard=True)
        elif type(struct) is list:
            if key == "*" or wildcard:
                for value in struct:
                    if type(value) in [dict, list]:
                        change(value, key_path, new_value, wildcard=wildcard)
            else:
                try:
                    index = int(key)
                except ValueError:
                    return
                if struct[index] in [dict, list]:
                    change(struct[index], key_path, new_value)
                else:
                    struct[index] = new_value
                    changes[0] += 1

    match = re.fullmatch(r"([^=]+)=(.+)", command_text, re.DOTALL)
    if not match:
        raise Exception(f"Bad command structure: '{command_text}'")
    key_path = match.group(1).split(".")
    new_value = yaml.safe_load(match.group(2))
    change(struct, key_path, new_value)
    return changes[0]
