#!/opt/python/python-2.7.3/bin/python
# -*- coding: utf-8 -*-
# Adapated by Zhang Zhe

import numpy as np
from scipy.interpolate import interp1d
import argparse


def dealer(filename, step=1.0e-3):
    
    if not step:
        step = 1.0e-3
    elif isinstance(step, list):
        step = step[0]

    data = np.loadtxt(filename)
    data[:, 0] = data[:, 0] - data[0, 0]
    n = np.ceil(data[-1, 0] / float(step))

    f = interp1d(data[:, 0], data[:, 1])
    x = np.arange(n) * step
    y = f(x)

    if filename.split('.')[-1] == "sek":
        x = np.arange(n+3) * step
        y = np.concatenate((y[3:0:-1], y))

    xs = ["   %.5e" % i for i in x]
    ys = ["   %.5e" % i for i in y]
    
    mdata = '\n'.join(p[0] + p[1] for p in zip(xs, ys))
    mf = file("m_" + filename, 'w')
    mf.write(mdata)
    mf.close()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('filename', nargs='+')
    parser.add_argument('--step', nargs=1, type=float)

    args = parser.parse_args()
    for fn in args.filename:
        dealer(fn, args.step)


if __name__ == "__main__":
    main()


