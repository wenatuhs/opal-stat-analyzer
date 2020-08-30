#!/opt/python/python-2.7.3/bin/python
# -*- coding: utf-8 -*-
# Adapated by Zhang Zhe

import sys
import bisect
import argparse

import numpy as np


def mirror(filename, pos):
    
    if not pos:
        pos = 4.6e-2

    data = np.loadtxt(filename)
    index = bisect.bisect(data[:, 0], pos)
    if not index:
        print "Current mirror position is smaller than the lower limit of\
               the data, please specify a larger mirror position."
        sys.exit(-1)
    elif index >= len(data[:, 0]):
        print "Current mirror position is larger than the upper limit of\
               the data, please specify a smaller mirror position."
        sys.exit(-1)
    index -= 1
    le = data.shape[0]
    ce = data[index, 0]

    mdata = np.empty((2 * (le - index) - 1, 2))
    mdata[le - index - 1:, :] = data[index:, :]
    for i in range(le - index -1):
        mdata[i, 0] = 2 * ce - mdata[2 * (le - index - 1) - i, 0]
        mdata[i, 1] = mdata[2 * (le - index - 1) - i, 1]
    
    np.savetxt("m_" + filename, mdata)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('filename', nargs='+')
    parser.add_argument('--pos', nargs=1, type=float, help='''mirror position''')

    args = parser.parse_args()
    for fn in args.filename:
        mirror(fn, args.pos)


if __name__ == "__main__":
    main()


