from root_utils.root_file_utils import *
import argparse
from pos_utils import *

ROOT.gROOT.SetBatch(True)


def get_args():
    parser = argparse.ArgumentParser(description='dump geometry of IWCD barrel PMTs from WCSim into numpy .npz file')
    parser.add_argument('input_file', type=str)
    parser.add_argument('output_file', type=str, default=None, nargs='?')
    args = parser.parse_args()
    return args


def geodump(input_file, output_file):
    print("input file:", str(input_file))
    print("output file:", str(output_file))

    wcsim = WCSimFile(input_file)


    np_pos_x_all_tubes = np.zeros(wcsim.num_pmts)
    np_pos_y_all_tubes = np.zeros(wcsim.num_pmts)
    np_pos_z_all_tubes = np.zeros(wcsim.num_pmts)
    np_dir_x_all_tubes = np.zeros(wcsim.num_pmts)
    np_dir_y_all_tubes = np.zeros(wcsim.num_pmts)
    np_dir_z_all_tubes = np.zeros(wcsim.num_pmts)

    np_pmt_index_all_tubes = np.arange(wcsim.num_pmts)

    np.random.shuffle(np_pmt_index_all_tubes)

    np_module_index_all_tubes = module_index(np_pmt_index_all_tubes)

    for i in range(len(np_pmt_index_all_tubes)):
        pmt = wcsim.geo.GetPMT(int(np_pmt_index_all_tubes[i]))
        np_pos_x_all_tubes[i] = pmt.GetPosition(0)
        np_pos_y_all_tubes[i] = pmt.GetPosition(1)
        np_pos_z_all_tubes[i] = pmt.GetPosition(2)
        np_dir_x_all_tubes[i] = pmt.GetOrientation(0)
        np_dir_y_all_tubes[i] = pmt.GetOrientation(1)
        np_dir_z_all_tubes[i] = pmt.GetOrientation(2)

    np_wall_indices = np.where(is_barrel(np_module_index_all_tubes))

    np_pos_x_wall_tubes = np_pos_x_all_tubes[np_wall_indices]
    np_pos_y_wall_tubes = np_pos_y_all_tubes[np_wall_indices]
    np_pos_z_wall_tubes = np_pos_z_all_tubes[np_wall_indices]
    np_dir_x_wall_tubes = np_dir_x_all_tubes[np_wall_indices]
    np_dir_y_wall_tubes = np_dir_y_all_tubes[np_wall_indices]
    np_dir_z_wall_tubes = np_dir_z_all_tubes[np_wall_indices]

    np_pmt_in_module_id_wall = pmt_in_module_id(np_pmt_index_all_tubes[np_wall_indices])
    np_wall_row, np_wall_col = row_col(np_module_index_all_tubes[np_wall_indices])

    np_wall_data_rect = np.zeros((16, 40, 19, 6))
    np_wall_data_rect[np_wall_row, np_wall_col, np_pmt_in_module_id_wall, 0] = np_pos_x_wall_tubes
    np_wall_data_rect[np_wall_row, np_wall_col, np_pmt_in_module_id_wall, 1] = np_pos_y_wall_tubes
    np_wall_data_rect[np_wall_row, np_wall_col, np_pmt_in_module_id_wall, 2] = np_pos_z_wall_tubes
    np_wall_data_rect[np_wall_row, np_wall_col, np_pmt_in_module_id_wall, 3] = np_dir_x_wall_tubes
    np_wall_data_rect[np_wall_row, np_wall_col, np_pmt_in_module_id_wall, 4] = np_dir_y_wall_tubes
    np_wall_data_rect[np_wall_row, np_wall_col, np_pmt_in_module_id_wall, 5] = np_dir_z_wall_tubes

    np.savez_compressed(output_file, geometry=np_wall_data_rect)


if __name__ == '__main__':
    ROOT.gSystem.Load(os.environ['WCSIMDIR'] + "/libWCSimRoot.so")
    config = get_args()

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
