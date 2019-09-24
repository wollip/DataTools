import ROOT
import os
import numpy as np

ROOT.gSystem.Load(os.environ['WCSIMDIR'] + "/libWCSimRoot.so")


class WCSim:
    def __init__(self, tree):
        print("number of entries in the geometry tree: " + str(self.geotree.GetEntries()))
        self.geotree.GetEntry(0)
        self.geo = self.geotree.wcsimrootgeom
        self.num_pmts = self.geo.GetWCNumPMT()
        self.tree = tree
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
        # Delete previous triggers to prevent memory leak (only if file does not change)
        triggers = [self.event.GetTrigger(i) for i in range(self.ntrigger)]
        oldfile = self.tree.GetCurrentFile()
        self.tree.GetEvent(ev)
        if self.tree.GetCurrentFile() == oldfile: [t.Delete() for t in triggers]
        self.current_event = ev
        self.event = self.tree.wcsimrootevent
        self.ntrigger = self.event.GetNumberOfEvents()

    def get_trigger(self, trig):
        self.trigger = self.event.GetTrigger(trig)
        self.current_trigger = trig
        return self.trigger

    def get_first_trigger(self):
        first_trigger = 0
        first_trigger_time = 9999999.0
        for index in range(self.ntrigger):
            self.get_trigger(index)
            trigger_time = self.trigger.GetHeader().GetDate()
            if trigger_time < first_trigger_time:
                first_trigger_time = trigger_time
                first_trigger = index
        return self.get_trigger(first_trigger)

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

    def get_digitized_hits(self):
        nhits = self.trigger.GetNcherenkovdigihits()
        hits = {
            "position": np.zeros((nhits,3)),
            "charge": np.zeros(nhits),
            "time": np.zeros(nhits),
            "pmt": np.zeros(nhits, dtype=np.int32)
        }
        for i in range(nhits):
            hit = self.trigger.GetCherenkovDigiHits().At(i)
            pmt_id = hit.GetTubeId() - 1
            pmt = self.geo.GetPMT(pmt_id)
            hits["position"][i] = [pmt.GetPosition(j) for j in range(3)]
            hits["charge"][i] = hit.GetQ()
            hits["time"][i] = hit.GetT()
            hits["pmt"][i] = pmt_id
        return hits

    def get_true_hits(self):
        nhits = self.trigger.GetNcherenkovhits()
        hits = {
            "position": np.zeros((nhits,3)),
            "track" : np.zeros(nhits),
            "pmt": np.zeros(nhits, dtype=np.int32),
            "PE": np.zeros(nhits)
        }
        for i in range(nhits):
            hit = self.trigger.GetCherenkovHits().At(i)
            pmt_id = hit.GetTubeID() - 1
            pmt = self.geo.GetPMT(pmt_id)
            tracks = set()
            for j in range(hit.GetTotalPe(0), hit.GetTotalPe(0)+hit.GetTotalPe(1)):
                pe = self.trigger.GetCherenkovHitTimes().At(j)
                tracks.add(pe.GetParentID())
            hits["position"][i] = [pmt.GetPosition(k) for k in range(3)]
            hits["track"][i] = tracks.pop() if len(tracks) == 1 else -2
            hits["pmt"][i] = pmt_id
            hits["PE"][i] = hit.GetTotalPe(1)

        return hits

    def get_hit_photons(self):
        nphotons = self.trigger.GetNcherenkovhittimes()
        photons = {
            "start_position": np.zeros((nphotons,3)),
            "end_position": np.zeros((nphotons,3)),
            "start_time": np.zeros(nphotons),
            "end_time": np.zeros(nphotons),
            "track": np.zeros(nphotons, dtype=np.int32),
            "pmt": np.zeros(nphotons, dtype=np.int32)
        }
        i = 0
        for hit in self.trigger.GetCherenkovHits():
            pmt_id = hit.GetTubeID() - 1
            for j in range(hit.GetTotalPe(0), hit.GetTotalPe(0)+hit.GetTotalPe(1)):
                pe = self.trigger.GetCherenkovHitTimes().At(j)
                photons["start_position"][i] = [pe.GetPhotonStartPos(j)/10 for j in range(3)]
                photons["end_position"][i] = [pe.GetPhotonEndPos(j)/10 for j in range(3)]
                photons["start_time"][i] = pe.GetPhotonStartTime()
                photons["end_time"][i] = pe.GetTruetime()
                photons["track"][i] = pe.GetParentID()
                photons["pmt"][i] = pmt_id
                i += 1
        return photons


class WCSimFile(WCSim):
    def __init__(self, filename):
        self.file = ROOT.TFile(filename, "read")
        tree = self.file.Get("wcsimT")
        self.geotree = self.file.Get("wcsimGeoT")
        super().__init__(tree)

    def __del__(self):
        self.file.Close()


class WCSimChain(WCSim):
    def __init__(self, filenames):
        self.chain = ROOT.TChain("wcsimT")
        for file in filenames:
            self.chain.Add(file)
        self.file = self.GetFile()
        self.geotree = self.file.Get("wcsimGeoT")
        super().__init__(self.chain)

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
