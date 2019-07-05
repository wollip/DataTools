import argparse
from root_utils.root_file_utils import *

ROOT.gROOT.SetBatch(True)


def get_args():
    parser = argparse.ArgumentParser(description='dump WCSim data into numpy .npz file')
    parser.add_argument('-i', '--input', action='append', nargs='+', metavar=('name' 'file(s)'))
    args = parser.parse_args()
    return args


def process_fileset(name, files):
    wcsim = WCSimChain(files)
    print(wcsim.nevent, "events in file set", name)
    digiHitTime = ROOT.TH1D("digiHitTime", name+";Digitized hit times [ns]", 1350, 550, 1900)
    digiHitCharge = ROOT.TH1D("digiHitCharge", name+";Digitized hit charge", 1000, 0.1, 100)
    totalCharge = ROOT.TH1D("totalCharge", name+";Total charge", 1000, 100, 100000)
    digiHitTime.SetStats(0)
    digiHitCharge.SetStats(0)
    totalCharge.SetStats(0)
    digiHitTime.GetXaxis().SetTitleSize(0.05)
    digiHitCharge.GetXaxis().SetTitleSize(0.05)
    totalCharge.GetXaxis().SetTitleSize(0.05)
    for ev in range(wcsim.nevent):
        if ev % 100 == 0: print("event", ev, "of", wcsim.nevent, flush=True)
        wcsim.get_event(ev)
        trigger = wcsim.get_first_trigger()
        ncherenkovdigihits = trigger.GetNcherenkovdigihits()
        totalQ = 0
        for i in range(ncherenkovdigihits):
            hit = trigger.GetCherenkovDigiHits().At(i)
            digiHitTime.Fill(hit.GetT())
            Q = hit.GetQ()
            totalQ += Q
            digiHitCharge.Fill(Q)
        totalCharge.Fill(totalQ)
    if not os.path.isdir(name):
        os.mkdir(name)
    path=os.path.abspath(name)
    c = ROOT.TCanvas()
    digiHitTime.Draw()
    c.SetLogy()
    c.SaveAs(path+"/digiHitTime.pdf")
    digiHitCharge.Draw()
    c.SetLogy()
    c.SetLogx()
    c.Draw()
    c.SaveAs(path+"/digiHitCharge.pdf")
    totalCharge.Draw()
    c.SetLogy()
    c.SetLogx()
    c.Draw()
    c.SaveAs(path+"/totalCharge.pdf")


if __name__ == '__main__':
    config = get_args()
    for fileset in config.input:
        process_fileset(fileset[0], fileset[1:])
