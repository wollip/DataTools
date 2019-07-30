from root_utils.root_file_utils import *
import argparse
import numpy as np

ROOT.gROOT.SetBatch(True)


def get_args():
    parser = argparse.ArgumentParser(description='dump geometry data from WCSim into numpy .npz file')
    parser.add_argument('input_file', type=str)
    parser.add_argument('output_file', type=str, default=None)
    args = parser.parse_args()
    return args


def geodump(input_file, output_file):

    print("input file:", input_file)
    print("output file:", output_file)
    
    file = WCSimFile(input_file)
    if config.output_file is None:
        config.output_file=config.input_file.replace(".root",".npz")
        print("set output file to: "+config.output_file)
    
    geo=file.geo
    
    num_pmts=geo.GetWCNumPMT()

    tube_no = np.zeros(num_pmts, dtype=int)
    position = np.zeros((num_pmts,3))
    orientation = np.zeros((num_pmts,3))

    for i in range(num_pmts):
        pmt=geo.GetPMT(i)
        tube_no[i] = pmt.GetTubeNo()
        for j in range(3):
            position[i][j] = pmt.GetPosition(j)
            orientation[i][j] = pmt.GetOrientation(j)

    np.savez_compressed(output_file, tube_no=tube_no, position=position, orientation=orientation)


if __name__ == '__main__':
    
    ROOT.gSystem.Load(os.environ['WCSIMDIR']+"/libWCSimRoot.so")
    config=get_args()

    if os.path.splitext(config.input_file)[1].lower() != '.root':
        print("File " + config.input_file + " is not a .root file")
        exit(1)
    input_file = os.path.abspath(config.input_file)

    if config.output_file is None:
        output_file = os.path.splitext(input_file)[0] + '.geo.npz'
        print("Output file not set, using", output_file)
    else:
        output_file = os.path.abspath(config.output_file)

    geodump(input_file, output_file)
