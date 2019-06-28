import ROOT
import os

ROOT.gROOT.SetBatch(True)
ROOT.gSystem.Load(os.environ['WCSIMDIR'] + "/libWCSimRoot.so")


class WCSimFile:
    def __init__(self, filename):
        self.file = ROOT.TFile(filename, "read")
        self.geotree = self.file.Get("wcsimGeoT")
        print("number of entries in the geometry tree: " + str(self.geotree.GetEntries()))
        self.geotree.GetEntry(0)
        self.geo = self.geotree.wcsimrootgeom
        self.num_pmts = self.geo.GetWCNumPMT()
        self.tree = self.file.Get("wcsimT")
        self.nevent = self.tree.GetEntries()
        print("number of entries in the tree: " + str(self.nevent))
        # Get first event and trigger to prevent segfault when later deleting trigger to prevent memory leak
        self.tree.GetEvent(0)
        self.current_event = 0
        self.event = self.tree.wcsimrootevent
        self.ntrigger = self.event.GetNumberOfEvents()
        self.trigger = self.event.GetTrigger(0)
        self.current_trigger = 0

    def get_event(self, ev):
        # Delete previous trigger to prevent memory leak
        self.trigger.Delete()
        self.tree.GetEvent(ev)
        self.current_event = ev
        self.event = self.tree.wcsimrootevent
        self.ntrigger = self.event.GetNumberOfEvents()

    def get_trigger(self, trig):
        self.trigger = self.event.GetTrigger(trig)
        self.current_trigger = trig
        return self.trigger

    def __del__(self):
        self.file.Close()

    def get_truth_info(self):
        self.get_trigger(0)
        tracks = self.trigger.GetTracks()
        energy = []
        position = []
        direction = []
        pid = []
        for i in range(self.trigger.GetNtrack()):
            if tracks[i].GetParenttype() == 0 and tracks[i].GetFlag() == 0 and tracks[i].GetIpnu() in [22, 11, -11, 13,
                                                                                                       -13, 111]:
                pid.append(tracks[i].GetIpnu())
                position.append([tracks[i].GetStart(0), tracks[i].GetStart(1), tracks[i].GetStart(2)])
                direction.append([tracks[i].GetDir(0), tracks[i].GetDir(1), tracks[i].GetDir(2)])
                energy.append(tracks[i].GetE())
        return direction, energy, pid, position

    def get_first_trigger(self):
        first_trigger = 0
        first_trigger_time = 9999999.0
        for index in range(self.ntrigger):
            self.get_trigger(index)
            trigger_time = min([hit.GetT() for hit in self.trigger.GetCherenkovDigiHits()])
            if trigger_time < first_trigger_time:
                first_trigger_time = trigger_time
                first_trigger = index
        return self.get_trigger(first_trigger)


def get_label(infile):
    if "_gamma" in infile:
        label = 0
    elif "_e" in infile:
        label = 1
    elif "_mu" in infile:
        label = 2
    elif "_pi0" in infile:
        label = 3
    else:
        print("Unknown input file particle type")
        raise SystemExit
    return label
