import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import LinearSegmentedColormap as lsc
from mpl_toolkits.axes_grid1 import ImageGrid

from pos_utils import *
from event_disp_and_dump_arg_utils import get_args

import ROOT
ROOT.gROOT.SetBatch(True)

import os


def geodump(config):

    config.input_file=config.input_file[0]
    print "input file: "+str(config.input_file)
    print "output file: "+str(config.output_file)
    
    #file=ROOT.TFile("mu_500MeV_run700_wcsim.root","read")
    file=ROOT.TFile(config.input_file,"read")
    if config.output_file is None:
        config.output_file=config.input_file.replace(".root",".npz")
        print "set output file to: "+config.output_file
    
    geotree=file.Get("wcsimGeoT");
    

    print "number of entries in the geometry tree: " + str(geotree.GetEntries())

    geotree.GetEntry(0)
    geo=geotree.wcsimrootgeom
    
    num_pmts=geo.GetWCNumPMT()

    np_pos_x_all_tubes=np.zeros((num_pmts))
    np_pos_y_all_tubes=np.zeros((num_pmts))
    np_pos_z_all_tubes=np.zeros((num_pmts))
    np_dir_x_all_tubes=np.zeros((num_pmts))
    np_dir_y_all_tubes=np.zeros((num_pmts))
    np_dir_z_all_tubes=np.zeros((num_pmts))
#    np_pmt_in_module_id=np.zeros((numpmts))
    np_pmt_index_all_tubes=np.arange(num_pmts)
    np.random.shuffle(np_pmt_index_all_tubes)
    np_module_index_all_tubes=module_index(np_pmt_index_all_tubes)

    for i in range(len(np_pmt_index_all_tubes)):
        
        pmt=geo.GetPMT(np_pmt_index_all_tubes[i])
        
        np_pos_x_all_tubes[i]=pmt.GetPosition(2)
        np_pos_y_all_tubes[i]=pmt.GetPosition(0)
        np_pos_z_all_tubes[i]=pmt.GetPosition(1)
        np_dir_x_all_tubes[i]=pmt.GetOrientation(2)
        np_dir_y_all_tubes[i]=pmt.GetOrientation(0)
        np_dir_z_all_tubes[i]=pmt.GetOrientation(1)
        
#        np_pmt_in_module_id[i]=pmt_in_module_id(np_pmt_index)

    np_wall_indices=np.where(is_barrel(np_module_index_all_tubes))
    
    np_pos_x_wall_tubes=np_pos_x_all_tubes[np_wall_indices]
    np_pos_y_wall_tubes=np_pos_y_all_tubes[np_wall_indices]
    np_pos_z_wall_tubes=np_pos_z_all_tubes[np_wall_indices]
    np_dir_x_wall_tubes=np_dir_x_all_tubes[np_wall_indices]
    np_dir_y_wall_tubes=np_dir_y_all_tubes[np_wall_indices]
    np_dir_z_wall_tubes=np_dir_z_all_tubes[np_wall_indices]

    np_pmt_in_module_id_wall=pmt_in_module_id(np_pmt_index_all_tubes[np_wall_indices])
    np_wall_row, np_wall_col=row_col(np_module_index_all_tubes[np_wall_indices])
        
    np_wall_data_rect=np.zeros((16,40,19,6))
    np_wall_data_rect[np_wall_row, np_wall_col, np_pmt_in_module_id_wall, 0]=np_pos_x_wall_tubes
    np_wall_data_rect[np_wall_row, np_wall_col, np_pmt_in_module_id_wall, 1]=np_pos_y_wall_tubes
    np_wall_data_rect[np_wall_row, np_wall_col, np_pmt_in_module_id_wall, 2]=np_pos_z_wall_tubes
    np_wall_data_rect[np_wall_row, np_wall_col, np_pmt_in_module_id_wall, 3]=np_dir_x_wall_tubes
    np_wall_data_rect[np_wall_row, np_wall_col, np_pmt_in_module_id_wall, 4]=np_dir_y_wall_tubes
    np_wall_data_rect[np_wall_row, np_wall_col, np_pmt_in_module_id_wall, 5]=np_dir_z_wall_tubes

    np.savez_compressed(config.output_file,geometry=np_wall_data_rect)

if __name__ == '__main__':
    
    ROOT.gSystem.Load(os.environ['WCSIMDIR']+"/libWCSimRoot.so")
    config=get_args()
    geodump(config)
    
