import argparse
from root_utils.root_file_utils import *


def get_args():
    parser = argparse.ArgumentParser(description='dump WCSim data into numpy .npz file')
    parser.add_argument('-i', '--input', action='append', nargs='+', metavar=('name' 'file(s)'))
    args = parser.parse_args()
    return args


def process_fileset(name, files):
    wcsim = WCSimChain(files)
    print(wcsim.nevent, "events in file set", name)


if __name__ == '__main__':
    config = get_args()
    for fileset in config.input:
        process_fileset(fileset[0], fileset[1:])
