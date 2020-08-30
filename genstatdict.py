#!/opt/python/python-2.7.3/bin/python
# -*- coding: utf-8 -*-
# Adapated by Zhang Zhe

import sys
from collections import OrderedDict

def genStatDict(filename="cBandGun.stat"):
    dic = OrderedDict()
    num = 0

    try:
        f = file(filename)
        while True:
            l = f.readline()
            if l:
                tokens = l.split()
                try:
                    if tokens[0] == "&column":
                        name = tokens[1].split('=')[1]
                        if name[-1] == ',':
                            name = name[:-1]
                        units = tokens[3].split('=')[1]
                        if units[-1] == ',':
                            units = units[:-1]
                        dic[name] = (num, 1, units)
                        num += 1 
                    elif tokens[0] == "OPAL":
                        break
                except IndexError:
                    pass
            else:
                break
        f.close()
    except IOError:
        sys.exit(-1)

    textdict = "statdict = {\n"
    for key in dic:
        textdict += "    '%s': %s" % (key, dic[key]) + ',\n'
    textdict += '}'

    f = file("statdict.py", 'w')
    f.write(textdict)
    f.close()


if __name__ == "__main__":
    genStatDict()
