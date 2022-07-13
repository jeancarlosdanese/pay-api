import re


camel_pat = re.compile(r"([A-Z])")
under_pat = re.compile(r"_([a-z])")


def camel_to_underscore(name):
    res = camel_pat.sub(lambda x: "_" + x.group(1).lower(), name)
    # print(f"{name}: --> {res}")
    return res


def underscore_to_camel(name):
    res = under_pat.sub(lambda x: x.group(1).upper(), name)
    # print(f"{name}: --> {res}")
    return res
