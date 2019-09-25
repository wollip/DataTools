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
        if self.tree.GetCurrentFile() == oldfile:
            [t.Delete() for t in triggers]
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

    def get_truth_info(self):  # deprecated: should now use get_event_info instead, leaving here for use with old files
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

    def get_event_info(self):
        self.get_trigger(0)
        tracks = self.trigger.GetTracks()
        primaries = [t for t in tracks if t.GetFlag() == 0 and t.GetParenttype() == 0]
        # Only one primary, this is the particle being simulated:
        if len(primaries) == 1:
            return {
                "pid": primaries[0].GetIpnu(),
                "position": [primaries[0].GetStart(i) for i in range(3)],
                "direction": [primaries[0].GetDir(i) for i in range(3)],
                "energy": primaries[0].GetE()
            }
        # Otherwise check for single incoming particle with flag -1:
        incoming = [t for t in tracks if t.GetFlag() == -1]
        if len(incoming) == 1:
            return {
                "pid": incoming[0].GetIpnu(),
                "position": [incoming[0].GetStart(i) for i in range(3)],
                "direction": [incoming[0].GetDir(i) for i in range(3)],
                "energy": incoming[0].GetE()
            }
        # Otherwise should be a positron/electron pair from a gamma simulation (temporary hack until gamma truth saved)
        if len(primaries) == 2 and abs(primaries[0].GetIpnu()) == 11 and abs(primaries[1].GetIpnu()) == 11:
            momentum = [sum(p.GetDir(i)*p.GetP() for p in primaries) for i in range(3)]
            norm = np.sqrt(sum(p**2 for p in momentum))
            return{
                "pid": 22,
                "position": [primaries[0].GetStart(i) for i in range(3)],  # e+ / e- should have same position
                "direction": [p/norm for p in momentum],
                "energy": sum(p.GetE() for p in primaries)
            }

    def get_digitized_hits(self):
        position = []
        charge = []
        time = []
        pmt = []
        trigger = []
        for t in range(self.ntrigger):
            self.get_trigger(t)
            for hit in self.trigger.GetCherenkovDigiHits():
                pmt_id = hit.GetTubeId() - 1
                position.append([self.geo.GetPMT(pmt_id).GetPosition(j) for j in range(3)])
                charge.append(hit.GetQ())
                time.append(hit.GetT())
                pmt.append(pmt_id)
                trigger.append(t)
        hits = {
            "position": np.asarray(position, dtype=np.float32),
            "charge": np.asarray(charge, dtype=np.float32),
            "time": np.asarray(time, dtype=np.float32),
            "pmt": np.asarray(pmt, dtype=np.int32),
            "trigger": np.asarray(trigger, dtype=np.int32)
        }
        return hits

    def get_true_hits(self):
        position = []
        track = []
        pmt = []
        PE = []
        trigger = []
        for t in range(self.ntrigger):
            self.get_trigger(t)
            for hit in self.trigger.GetCherenkovHits():
                pmt_id = hit.GetTubeID() - 1
                tracks = set()
                for j in range(hit.GetTotalPe(0), hit.GetTotalPe(0)+hit.GetTotalPe(1)):
                    pe = self.trigger.GetCherenkovHitTimes().At(j)
                    tracks.add(pe.GetParentID())
                position.append([self.geo.GetPMT(pmt_id).GetPosition(k) for k in range(3)])
                track.append(tracks.pop() if len(tracks) == 1 else -2)
                pmt.append(pmt_id)
                PE.append(hit.GetTotalPe(1))
                trigger.append(t)
        hits = {
            "position": np.asarray(position, dtype=np.float32),
            "track": np.asarray(track, dtype=np.int32),
            "pmt": np.asarray(pmt, dtype=np.int32),
            "PE": np.asarray(PE, dtype=np.int32),
            "trigger": np.asarray(trigger, dtype=np.int32)
        }
        return hits

    def get_hit_photons(self):
        start_position = []
        end_position = []
        start_time = []
        end_time = []
        track = []
        pmt = []
        trigger = []
        for t in range(self.ntrigger):
            self.get_trigger(t)
            for hit in self.trigger.GetCherenkovHits():
                pmt_id = hit.GetTubeID() - 1
                for j in range(hit.GetTotalPe(0), hit.GetTotalPe(0)+hit.GetTotalPe(1)):
                    pe = self.trigger.GetCherenkovHitTimes().At(j)
                    try:  # Only works with new tracking branch of WCSim
                        start_position.append([pe.GetPhotonStartPos(j)/10 for j in range(3)])
                        end_position.append([pe.GetPhotonEndPos(j)/10 for j in range(3)])
                        start_time.append(pe.GetPhotonStartTime())
                    except AttributeError:
                        start_position.append([0, 0, 0])
                        end_position.append([0, 0, 0])
                        start_time.append(0)
                    end_time.append(pe.GetTruetime())
                    track.append(pe.GetParentID())
                    pmt.append(pmt_id)
                    trigger.append(t)
        photons = {
            "start_position": np.asarray(start_position, dtype=np.float32),
            "end_position": np.asarray(end_position, dtype=np.float32),
            "start_time": np.asarray(start_time, dtype=np.float32),
            "end_time": np.asarray(end_time, dtype=np.float32),
            "track": np.asarray(track, dtype=np.int32),
            "pmt": np.asarray(pmt, dtype=np.int32),
            "trigger": np.asarray(trigger, dtype=np.int32)
        }
        return photons

    def get_tracks(self):
        id = []
        pid = []
        start_time = []
        energy = []
        start_position = []
        stop_position = []
        parent = []
        for t in range(self.ntrigger):
            self.get_trigger(t)
            for track in self.trigger.GetTracks():
                id.append(track.GetId())
                pid.append(track.GetIpnu())
                start_time.append(track.GetTime())
                energy.append(track.GetE())
                start_position.append([track.GetStart(i) for i in range(3)])
                stop_position.append([track.GetStop(i) for i in range(3)])
                parent.append(track.GetParenttype())
        tracks = {
            "id": np.asarray(id, dtype=np.int32),
            "pid": np.asarray(pid, dtype=np.int32),
            "start_time": np.asarray(start_time, dtype=np.float32),
            "energy": np.asarray(energy, dtype=np.float32),
            "start_position": np.asarray(start_position, dtype=np.float32),
            "stop_position": np.asarray(stop_position, dtype=np.float32),
            "parent": np.asarray(parent, dtype=np.int32)
        }
        return tracks

    def get_trigger_times(self):
        trigger_times = np.empty(self.ntrigger, dtype=np.float32)
        for t in range(self.ntrigger):
            self.get_trigger(t)
            trigger_times[t] = self.trigger.GetHeader().GetDate()
        return trigger_times


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
