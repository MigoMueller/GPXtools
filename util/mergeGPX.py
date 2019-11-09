#!/usr/bin/env python

import gpxTools
import sys
import os

if __name__=="__main__":
    if len(sys.argv) < 4:
        print("Usage: ", sys.argv[0], " outputFileName inputFiles")
        assert False
    outputFileName=sys.argv[1]
    assert not os.path.isfile(outputFileName)
    for f in sys.argv[2:]:
        assert os.path.isfile(f)
    bla=gpxTools.gpxTools()
    bla.mergeTracks(sys.argv[2:], outputFileName)
    print('done')
