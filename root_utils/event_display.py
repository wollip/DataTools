"""
Python 3 script for displaying data from a particular event in a ROOT file at a specified index

Authors: Wojtek Fedorko, Julian Ding, Nick Prouse
"""
import argparse

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap as lsc
from mpl_toolkits.axes_grid1 import ImageGrid
from mpl_toolkits.mplot3d import Axes3D

from root_utils.pos_utils import *
from root_utils.root_file_utils import *

import os

ROOT.gROOT.SetBatch(True)

matplotlib.use('Agg')


def get_args():
    parser = argparse.ArgumentParser(description='Display events from a list of input ROOT files')
    parser.add_argument('input_file', type=str)
    parser.add_argument('output_dir', type=str)
    args = parser.parse_args()
    return args


def scatter_plot(num, x, y, c, s, cm, xlabel, ylabel, label, filename, norm=None, ticks=None):
    fig = plt.figure(num=num, clear=True)
    fig.set_size_inches(10, 8)
    ax = fig.add_subplot(111)
    plot = ax.scatter(x, y, c=c, s=s, cmap=cm, norm=norm, marker='.')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    cbar = fig.colorbar(plot, ticks=ticks, pad=0.1)
    cbar.set_label(label)
    fig.savefig(filename)

def event_display(ev, input_file, write_dir):

    norm = plt.Normalize()

    cm = matplotlib.cm.plasma

    cmaplist = [cm(i) for i in range(cm.N)]
    cm_cat_pmt_in_module = lsc.from_list('Custom cmap', cmaplist, cm.N)
    bounds_cat_pmt_in_module = np.linspace(0, 19, 20)
    norm_cat_pmt_in_module = matplotlib.colors.BoundaryNorm(bounds_cat_pmt_in_module, cm_cat_pmt_in_module.N)
    cm_cat_module_row = lsc.from_list('Custom cmap', cmaplist, cm.N)
    bounds_cat_module_row = np.linspace(0, 16, 17)
    norm_cat_module_row = matplotlib.colors.BoundaryNorm(bounds_cat_module_row, cm_cat_module_row.N)
    cm_cat_module_col = lsc.from_list('Custom cmap', cmaplist, cm.N)
    bounds_cat_module_col = np.linspace(0, 40, 41)
    norm_cat_module_col = matplotlib.colors.BoundaryNorm(bounds_cat_module_col, cm_cat_module_col.N)

    wcsim = WCSimFile(input_file)

    np_pos_x_all_tubes = np.zeros(wcsim.num_pmts)
    np_pos_y_all_tubes = np.zeros(wcsim.num_pmts)
    np_pos_z_all_tubes = np.zeros(wcsim.num_pmts)

    np_pmt_in_module_id_all_tubes = np.zeros(wcsim.num_pmts)
    np_pmt_index_all_tubes = np.arange(wcsim.num_pmts)

    np.random.shuffle(np_pmt_index_all_tubes)

    np_module_index_all_tubes = module_index(np_pmt_index_all_tubes)

    for i in range(len(np_pmt_index_all_tubes)):
        pmt_tube_in_module_id = np_pmt_index_all_tubes[i] % 19
        np_pmt_in_module_id_all_tubes[i] = pmt_tube_in_module_id
        pmt = wcsim.geo.GetPMT(int(np_pmt_index_all_tubes[i]))

        np_pos_x_all_tubes[i] = pmt.GetPosition(2)
        np_pos_y_all_tubes[i] = pmt.GetPosition(0)
        np_pos_z_all_tubes[i] = pmt.GetPosition(1)

    np_pos_r_all_tubes = np.hypot(np_pos_x_all_tubes, np_pos_y_all_tubes)

    r_max = np.amax(np_pos_r_all_tubes)

    np_pos_phi_all_tubes = np.arctan2(np_pos_y_all_tubes, np_pos_x_all_tubes)
    np_pos_arc_all_tubes = r_max * np_pos_phi_all_tubes

    np_wall_indices = np.where(is_barrel(np_module_index_all_tubes))
    np_top_indices = np.where(is_top(np_module_index_all_tubes))
    np_bottom_indices = np.where(is_bottom(np_module_index_all_tubes))

    np_pmt_in_module_id_wall_tubes = np_pmt_in_module_id_all_tubes[np_wall_indices]
    np_pmt_in_module_id_top_tubes = np_pmt_in_module_id_all_tubes[np_top_indices]
    np_pmt_in_module_id_bottom_tubes = np_pmt_in_module_id_all_tubes[np_bottom_indices]

    np_pos_z_wall_tubes = np_pos_z_all_tubes[np_wall_indices]
    np_pos_x_top_tubes = np_pos_x_all_tubes[np_top_indices]
    np_pos_y_top_tubes = np_pos_y_all_tubes[np_top_indices]
    np_pos_x_bottom_tubes = np_pos_x_all_tubes[np_bottom_indices]
    np_pos_y_bottom_tubes = np_pos_y_all_tubes[np_bottom_indices]

    np_wall_row, np_wall_col = row_col(np_module_index_all_tubes[np_wall_indices])

    np_pos_arc_wall_tubes = np_pos_arc_all_tubes[np_wall_indices]

    scatter_plot(101, np_pos_arc_all_tubes, np_pos_z_all_tubes, np_pmt_in_module_id_all_tubes, 5, cm_cat_pmt_in_module,
                 'arc along the wall', 'z', "pmt in module", os.path.join(write_dir,"pos_arc_z_disp_all_tubes.pdf"),
                 norm_cat_pmt_in_module, range(20))

    scatter_plot(102, np_pos_x_all_tubes, np_pos_y_all_tubes, np_pmt_in_module_id_all_tubes, 5, cm_cat_pmt_in_module,
                 'x', 'y', "pmt in module", os.path.join(write_dir,"pos_x_y_disp_all_tubes.pdf"), norm_cat_pmt_in_module, range(20))

    scatter_plot(103, np_pos_arc_wall_tubes, np_pos_z_wall_tubes, np_pmt_in_module_id_wall_tubes, 5,
                 cm_cat_pmt_in_module, 'arc along the wall', 'z', "pmt in module",
                 os.path.join(write_dir,"pos_arc_z_disp_wall_tubes.pdf"), norm_cat_pmt_in_module, range(20))

    scatter_plot(104, np_pos_arc_wall_tubes, np_pos_z_wall_tubes, np_wall_row, 5, cm_cat_module_row,
                 'arc along the wall', 'z', "wall module row", os.path.join(write_dir,"pos_arc_z_disp_wall_tubes_color_row.pdf"),
                 norm_cat_module_row, range(16))

    scatter_plot(105, np_pos_arc_wall_tubes, np_pos_z_wall_tubes, np_wall_col, 5, cm_cat_module_col,
                 'arc along the wall', 'z', "wall module column", os.path.join(write_dir,"pos_arc_z_disp_wall_tubes_color_col.pdf"),
                 norm_cat_module_col, range(40))

    scatter_plot(106, np_pos_x_top_tubes, np_pos_y_top_tubes, np_pmt_in_module_id_top_tubes, 5, cm_cat_pmt_in_module,
                 'x', 'y', "pmt in module", os.path.join(write_dir,"pos_x_y_disp_top_tubes.pdf"), norm_cat_pmt_in_module, range(20))

    scatter_plot(107, np_pos_x_bottom_tubes, np_pos_y_bottom_tubes, np_pmt_in_module_id_bottom_tubes, 5,
                 cm_cat_pmt_in_module, 'x', 'y', "pmt in module", os.path.join(write_dir,"pos_x_y_disp_bottom_tubes.pdf"),
                 norm_cat_pmt_in_module, range(20))

    wcsim.get_event(ev)
    print("number of triggers: " + str(wcsim.ntrigger))
    trigger = wcsim.get_first_trigger()
    print("event date and number: " + str(trigger.GetHeader().GetDate()) + " " + str(trigger.GetHeader().GetEvtNum()))
    ncherenkovdigihits = trigger.GetNcherenkovdigihits()
    print("Ncherenkovdigihits " + str(ncherenkovdigihits))
    if ncherenkovdigihits == 0:
        print("event, trigger has no hits " + str(ev) + " " + str(wcsim.current_trigger))

    np_pos_x = np.zeros(ncherenkovdigihits)
    np_pos_y = np.zeros(ncherenkovdigihits)
    np_pos_z = np.zeros(ncherenkovdigihits)

    np_dir_u = np.zeros(ncherenkovdigihits)
    np_dir_v = np.zeros(ncherenkovdigihits)
    np_dir_w = np.zeros(ncherenkovdigihits)

    np_q = np.zeros(ncherenkovdigihits)
    np_t = np.zeros(ncherenkovdigihits)

    np_pmt_index = np.zeros(ncherenkovdigihits, dtype=np.int32)

    for i in range(ncherenkovdigihits):
        wcsimrootcherenkovdigihit = trigger.GetCherenkovDigiHits().At(i)

        hit_q = wcsimrootcherenkovdigihit.GetQ()
        hit_t = wcsimrootcherenkovdigihit.GetT()
        hit_tube_id = wcsimrootcherenkovdigihit.GetTubeId() - 1

        np_pmt_index[i] = hit_tube_id

        # if i<10:
        #    print("q t id: "+str(hit_q)+" "+str(hit_t)+" "+str(hit_tube_id)+" ")

        pmt = wcsim.geo.GetPMT(hit_tube_id)

        # if i<10:
        #    print("pmt tube no: "+str(pmt.GetTubeNo()) #+" " +pmt.GetPMTName())
        #    print("pmt cyl loc: "+str(pmt.GetCylLoc()))

        # np_cylloc[i]=pmt.GetCylLoc()

        np_pos_x[i] = pmt.GetPosition(2)
        np_pos_y[i] = pmt.GetPosition(0)
        np_pos_z[i] = pmt.GetPosition(1)

        np_dir_u[i] = pmt.GetOrientation(2)
        np_dir_v[i] = pmt.GetOrientation(0)
        np_dir_w[i] = pmt.GetOrientation(1)

        np_q[i] = hit_q
        np_t[i] = hit_t

    np_module_index = module_index(np_pmt_index)
    np_pmt_in_module_id = pmt_in_module_id(np_pmt_index)
    np_wall_indices = np.where(is_barrel(np_module_index))
    np_top_indices = np.where(is_top(np_module_index))
    np_bottom_indices = np.where(is_bottom(np_module_index))

    np_pos_phi = np.arctan2(np_pos_y, np_pos_x)
    np_pos_arc = r_max * np_pos_phi
    np_pos_arc_wall = np_pos_arc[np_wall_indices]
    np_pos_x_top = np_pos_x[np_top_indices]
    np_pos_y_top = np_pos_y[np_top_indices]
    np_pos_x_bottom = np_pos_x[np_bottom_indices]
    np_pos_y_bottom = np_pos_y[np_bottom_indices]
    np_pos_z_wall = np_pos_z[np_wall_indices]

    np_q_top = np_q[np_top_indices]
    np_q_bottom = np_q[np_bottom_indices]
    np_q_wall = np_q[np_wall_indices]
    np_t_wall = np_t[np_wall_indices]

    np_wall_row, np_wall_col = row_col(np_module_index[np_wall_indices])
    np_pmt_in_module_id_wall = np_pmt_in_module_id[np_wall_indices]
    np_wall_data_rect = np.zeros((16, 40, 38))
    np_wall_data_rect[np_wall_row,
                      np_wall_col,
                      np_pmt_in_module_id_wall] = np_q_wall
    np_wall_data_rect[np_wall_row,
                      np_wall_col,
                      np_pmt_in_module_id_wall + 19] = np_t_wall
    np_wall_q_max_module = np.amax(np_wall_data_rect[:, :, 0:19], axis=-1)
    np_wall_q_sum_module = np.sum(np_wall_data_rect[:, :, 0:19], axis=-1)

    max_q = np.amax(np_q)
    np_scaled_q = 500 * np_q / max_q
    np_dir_u_scaled = np_dir_u * np_scaled_q
    np_dir_v_scaled = np_dir_v * np_scaled_q
    np_dir_w_scaled = np_dir_w * np_scaled_q

    fig1 = plt.figure(num=1, clear=True)
    fig1.set_size_inches(10, 8)
    ax1 = fig1.add_subplot(111, projection='3d', azim=35, elev=20)
    ev_disp = ax1.scatter(np_pos_x, np_pos_y, np_pos_z, c=np_q, s=2, alpha=0.4, cmap=cm, marker='.')
    ax1.set_xlabel('x')
    ax1.set_ylabel('y')
    ax1.set_zlabel('z')
    cb_ev_disp = fig1.colorbar(ev_disp, pad=0.03)
    cb_ev_disp.set_label("charge")
    fig1.savefig(os.path.join(write_dir,"ev_disp_ev_{}_trig_{}.pdf".format(ev, wcsim.current_trigger)))

    fig2 = plt.figure(num=2, clear=True)
    fig2.set_size_inches(10, 8)
    ax2 = fig2.add_subplot(111, projection='3d', azim=35, elev=20)
    colors = plt.cm.spring(norm(np_t))
    ax2.quiver(np_pos_x, np_pos_y, np_pos_z,
               np_dir_u_scaled, np_dir_v_scaled, np_dir_w_scaled,
               colors=colors, alpha=0.4, cmap=cm)
    ax2.set_xlabel('x')
    ax2.set_ylabel('y')
    ax2.set_zlabel('z')
    sm = matplotlib.cm.ScalarMappable(cmap=cm, norm=norm)
    sm.set_array([])
    cb_ev_disp_2 = fig2.colorbar(sm, pad=0.03)
    cb_ev_disp_2.set_label("time")
    fig2.savefig(os.path.join(write_dir,"ev_disp_quiver_ev_{}_trig_{}.pdf".format(ev, wcsim.current_trigger)))

    scatter_plot(3, np_pos_arc_wall, np_pos_z_wall, np_q_wall, 2, cm, 'arc along the wall', 'z', "charge",
                 os.path.join(write_dir,"ev_disp_wall_ev_{}_trig_{}.pdf".format(ev, wcsim.current_trigger)))

    scatter_plot(4, np_pos_x_top, np_pos_y_top, np_q_top, 2, cm, 'x', 'y', "charge",
                 os.path.join(write_dir,"ev_disp_top_ev_{}_trig_{}.pdf".format(ev, wcsim.current_trigger)))

    scatter_plot(5, np_pos_x_bottom, np_pos_y_bottom, np_q_bottom, 2, cm, 'x', 'y', "charge",
                 os.path.join(write_dir,"ev_disp_bottom_ev_{}_trig_{}.pdf".format(ev, wcsim.current_trigger)))

    fig6 = plt.figure(num=6, clear=True)
    fig6.set_size_inches(10, 4)
    ax6 = fig6.add_subplot(111)
    q_sum_disp = ax6.imshow(np.flip(np_wall_q_sum_module, axis=0), cmap=cm)
    ax6.set_xlabel('arc index')
    ax6.set_ylabel('z index')
    cb_q_sum_disp = fig6.colorbar(q_sum_disp, pad=0.1)
    cb_q_sum_disp.set_label("total charge in module")
    fig6.savefig(os.path.join(write_dir,"q_sum_disp_ev_{}_trig_{}.pdf".format(ev, wcsim.current_trigger)))

    fig7 = plt.figure(num=7, clear=True)
    fig7.set_size_inches(10, 4)
    ax7 = fig7.add_subplot(111)
    q_max_disp = ax7.imshow(np.flip(np_wall_q_max_module, axis=0), cmap=cm)
    ax7.set_xlabel('arc index')
    ax7.set_ylabel('z index')
    cb_q_max_disp = fig7.colorbar(q_max_disp, pad=0.1)
    cb_q_max_disp.set_label("maximum charge in module")
    fig7.savefig(os.path.join(write_dir,"q_max_disp_ev_{}_trig_{}.pdf".format(ev, wcsim.current_trigger)))

    fig8 = plt.figure(num=8, clear=True)
    fig8.set_size_inches(10, 8)
    ax8 = fig8.add_subplot(111)
    plt.hist(np_q, 50, density=True, facecolor='blue', alpha=0.75)
    ax8.set_xlabel('charge')
    ax8.set_ylabel("PMT's above threshold")
    fig8.savefig(os.path.join(write_dir,"q_pmt_disp_ev_{}_trig_{}.pdf".format(ev, wcsim.current_trigger)))

    fig9 = plt.figure(num=9, clear=True)
    fig9.set_size_inches(10, 8)
    ax9 = fig9.add_subplot(111)
    plt.hist(np_t, 50, density=True, facecolor='blue', alpha=0.75)
    ax9.set_xlabel('time')
    ax9.set_ylabel("PMT's above threshold")
    fig9.savefig(os.path.join(write_dir,"t_pmt_disp_ev_{}_trig_{}.pdf".format(ev, wcsim.current_trigger)))

    fig10 = plt.figure(num=10, clear=True)
    fig10.set_size_inches(15, 5)
    grid_q = ImageGrid(fig10, 111,
                       nrows_ncols=(4, 5),
                       axes_pad=0.0,
                       share_all=True,
                       label_mode="L",
                       cbar_location="top",
                       cbar_mode="single",
                       )
    for i in range(19):
        grid_q[i].imshow(np.flip(np_wall_data_rect[:, :, i], axis=0), cmap=cm)
        q_disp = grid_q[19].imshow(np.flip(np_wall_q_max_module, axis=0), cmap=cm)
        grid_q.cbar_axes[0].colorbar(q_disp)
    fig10.savefig(os.path.join(write_dir,"q_disp_grid_ev_{}_trig_{}.pdf".format(ev, wcsim.current_trigger)))

    fig11 = plt.figure(num=11, clear=True)
    fig11.set_size_inches(15, 5)
    grid_t = ImageGrid(fig11, 111,
                       nrows_ncols=(4, 5),
                       axes_pad=0.0,
                       share_all=True,
                       label_mode="L",
                       cbar_location="top",
                       cbar_mode="single",
                       )
    for i in range(19):
        grid_t[i].imshow(np.flip(np_wall_data_rect[:, :, i + 19], axis=0), cmap=cm)
    fig11.savefig(os.path.join(write_dir,"t_disp_grid_ev_{}_trig_{}.pdf".format(ev, wcsim.current_trigger)))


if __name__ == '__main__':
    config = get_args()
    print("output directory: " + str(config.output_dir))
    if not os.path.exists(config.output_dir):
        print("                  (does not exist... creating new directory)")
        os.mkdir(config.output_dir)
    if not os.path.isdir(config.output_dir):
        raise argparse.ArgumentTypeError("Cannot access or create output directory" + config.output_dir)

    print("Reading request from: " + str(config.input_file))

    wl = open(config.input_file, 'r')
    for line in wl:
        splits = line.split()
        name = splits[0].strip()
        input_file = splits[1].strip()
        ev = int(splits[2].strip())

        print("now processing " + input_file + " at index " + str(ev))

        labels = ["gamma", "e-", "mu-", "pi0"]
        write_dir = os.path.join(config.output_dir, labels[get_label(input_file)] + '_' + str(name))
        if not os.path.isdir(write_dir):
            os.mkdir(write_dir)

        event_display(ev, input_file, write_dir)

    wl.close()