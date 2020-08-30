#!/opt/python/python-2.7.3/bin/python
# -*- coding: utf-8 -*-
# Adapated by Zhang Zhe

import sys
import bisect
import argparse

import numpy as np


def zero(filename, pos):
    
    if not pos:
        pos = -4.6e-2

    data = np.loadtxt(filename)
    index = bisect.bisect(data[:, 0], pos)
    if not index:
        print "Current zero position is smaller than the lower limit of\
               the data, please specify a larger zero position."
        sys.exit(-1)
    elif index >= len(data[:, 0]):
        print "Current zero position is larger than the upper limit of\
               the data, please specify a smaller zero position."
        sys.exit(-1)
    index -= 1

    mdata = data[index:, :]
    le = mdata.shape[0]
    cdata = np.zeros(le)
    cdata[:index + 1] = data[index::-1, 1]
    mdata[:, 1] = mdata[:, 1] - cdata

    np.savetxt("z_" + filename, mdata)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('filename', nargs='+')
    parser.add_argument('--pos', nargs=1, type=float, help='''zero position''')

    args = parser.parse_args()
    for fn in args.filename:
        zero(fn, args.pos)


if __name__ == "__main__":
    main()


