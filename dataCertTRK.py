#! /usr/bin/env python
################################################################################
# This version has been modified to use information from TRACKER workspace instead of the GLOBAL one
# It can be that this version is not perfectly aligned with the official one available in git
# https://github.com/cms-dqm/certTools
# 
# $Author: smaruyam $
# $Date: 2012/12/14 17:02:45 $
# $Revision: 1.15 $ 18.06.2015 $
#
#
# Marco Rovere = marco.rovere@cern.ch
# Laura Borello = Laura.Borrello@cern.ch 
# Ringaile Placakyte = ringaile@mail.desy.de
#
################################################################################
from operator import itemgetter
import re, json, sys, ConfigParser, os, string, commands, time, socket

class Certifier():
    cfg='runreg.cfg'
    OnlineRX = "%Online%ALL"
    EXCL_LS_BITS = ('jetmet','muon','egamma')

    def __init__(self,argv,verbose=False):
        self.verbose = verbose
        if len(argv)==2:
            self.cfg = argv[1]
        else:
            self.cfg = Certifier.cfg
        self.qry = {}
        self.qry.setdefault("GOOD", "isNull OR = true")
        self.qry.setdefault("BAD", " = false")
        self.readConfig()

    def readConfig(self):
        CONFIG = ConfigParser.ConfigParser()
        if self.verbose:
            print 'Reading configuration file from %s' % self.cfg
        CONFIG.read(self.cfg)
        cfglist = CONFIG.items('Common')
        self.dataset = CONFIG.get('Common','DATASET')
        self.group   = CONFIG.get('Common','GROUP')
        self.address = CONFIG.get('Common','RUNREG')
        self.runmin  = CONFIG.get('Common','RUNMIN')
        self.runmax  = CONFIG.get('Common','RUNMAX')
        self.inputfile = CONFIG.get('Common','INPUTFILE')

        self.runlist = []
        if (self.inputfile != 'INPUTFILE'):
            import csv
            with open(self.inputfile, 'rb') as f:
                reader = csv.reader(f)
                self.runlist = [int(entry) for entry in list(reader)[0]]

        self.qflist  = CONFIG.get('Common','QFLAGS').split(',')

        self.bfield_thr  = '-0.1'
        self.bfield_min  = '-0.1'
        self.bfield_max  = '4.1'

        #self.dcslist = CONFIG.get('Common','DCS').split(',')

        if CONFIG.get('Common','QFLAGS').split(',') == ['NONE:NONE']:
          self.jsonfile = CONFIG.get('Common','JSONFILENQ')
        else:
          self.jsonfile = CONFIG.get('Common','JSONFILE')

        self.beamene     = []
        self.dbs_pds_all = ""
        self.online_cfg  = "FALSE"
        self.usedbs = False
        self.useDAS = False
        self.dsstate = ""
        self.useDBScache = "False"
        self.useBeamPresent = "False"
        self.useBeamStable = "False"
        self.cacheFiles = []
        self.predefinedPD = ["/Commissioning/Run2015A-v1/RAW","/ZeroBias/Run2015B-v1/RAW"]
        self.component = []
        self.nolowpu = "True"

        print "First run ", self.runmin
        print "Last run ", self.runmax
        if len(self.runlist)>0:
            print "List of runs ", self.runlist, " (",len(self.runlist), " runs)"
        print "Dataset name ", self.dataset
        print "Group name ", self.group
        print "Quality flags ", self.qflist
        #print "DCS flags ", self.dcslist

        for item in cfglist:
            if "BFIELD_THR" in item[0].upper():
                self.bfield_thr = item[1]
            if "BFIELD_MIN" in item[0].upper():
                self.bfield_min = item[1]
            if "BFIELD_MAX" in item[0].upper():
                self.bfield_max = item[1]
            if "BEAM_ENE" in item[0].upper():
                self.beamene = item[1].split(',')
            if "DBS_PDS" in item[0].upper():
                self.dbs_pds_all = item[1]
                self.usedbs = True
            if "USE_DAS" in item[0].upper():
                self.useDAS = item[1]
            if "ONLINE" in item[0].upper():
                self.online_cfg = item[1]
            if "DSSTATE" in item[0].upper():
                self.dsstate = item[1]
            if "DBSCACHE" in item[0].upper():
                self.useDBScache = item[1]
            if "BEAMPRESENT" in item[0].upper():
                self.useBeamPresent = item[1]
                print 'Use Beam Present Flag', self.useBeamPresent
            if "BEAMSTABLE" in item[0].upper():
                self.useBeamStable = item[1]
                print 'Use Beam Stable Flag', self.useBeamStable
            if "CACHEFILE" in item[0].upper():
                self.cacheFiles = item[1].split(',')
            if "COMPONENT" in item[0].upper():
                self.component = item[1].split(',')
                print 'COMPONENT ', self.component
            if "NOLOWPU" in item[0].upper():
                self.nolowpu = item[1]
                print 'NoLowPU', self.nolowpu

        self.dbs_pds = self.dbs_pds_all.split(",")

        if self.useDAS == "True":
            self.usedbs = False
        print "Using DAS database: ", self.useDAS
        print "Using Cache? : ", self.useDBScache

        self.online = False
        if "TRUE" == self.online_cfg.upper() or \
               "1" == self.online_cfg.upper() or \
               "YES" == self.online_cfg.upper():
            self.online = True

        try:
            self.bfield_min = float(self.bfield_min)
        except:
            print "Minimum BFIELD value not understood: ", self.bfield_min
            sys.exit(1)
        try:
            self.bfield_max = float(self.bfield_max)
        except:
            print "Maximum BFIELD value not understood: ", self.bfield_max
            sys.exit(1)
        try:
            self.bfield_thr = float(self.bfield_thr)
        except:
            print "Threshold BFIELD value not understood: ", self.bfield_thr
            sys.exit(1)
        if self.bfield_thr > self.bfield_min:
            self.bfield_min = self.bfield_thr

        for e in range(0, len(self.beamene)):
            try:
                self.beamene[e] = float(self.beamene[e])
                if self.verbose:
                    print "Beam Energy ", self.beamene
            except:
                print "BEAMENE value not understood: ", self.beamene
                sys.exit(1)
    def writeQuery(self):
        q  = "select r.RLR_RUN_NUMBER,r.RLR_SECTION_FROM,r.RLR_SECTION_TO from runreg_tracker.run_lumis r, runreg_tracker.runs o where"
        q  = q + " r.RLR_RUN_NUMBER   >= %s AND r.RLR_RUN_NUMBER <= %s" % (self.runmin,self.runmax)
        q  = q + " AND r.BEAM1_STABLE = 1 AND r.BEAM2_STABLE = 1"
        q  = q + " AND o.BFIELD       >= %i AND o.BFIELD <= %i" %(self.bfield_min,self.bfield_max)
        q  = q + " AND o.LHCENERGY    > %i - 400 AND o.LHCENERGY < %i + 400" % (self.beamene[0],self.beamene[0])
        q  = q + " AND o.RUNNUMBER    = r.RLR_RUN_NUMBER "
        q  = q + " AND r.CMS_ACTIVE   = 1"
        #q  = q + " AND ( (r.TIBTID_READY = 1 OR r.TOB_READY = 1 OR r.TECP_READY = 1 OR r.TECM_READY = 1) AND (r.BPIX_READY = 1 OR r.FPIX_READY = 1))"
        q  = q + " AND (r.TIBTID_READY = 1 OR r.TOB_READY = 1 OR r.TECP_READY = 1 OR r.TECM_READY = 1 OR r.BPIX_READY = 1 OR r.FPIX_READY = 1)"
        if (self.qflist[0] == "GOOD:GOOD"):
                q  = q + " AND (r.TIBTID_READY = 1 AND r.TOB_READY = 1 AND r.TECP_READY = 1 AND r.TECM_READY = 1 AND r.BPIX_READY = 1 AND r.FPIX_READY = 1 )"
        self.query = q
    def writeJSON(self):
        from rhapi import DEFAULT_URL, RhApi
        api = RhApi(DEFAULT_URL, debug = False)

        p = {"class": self.group}
        results = api.json_all(self.query, p)
        #print results
        json_ = {}
        for entry in results:
          try:
                json_[str(entry[0])].append([entry[1],entry[2]])
          except:
                json_[str(entry[0])] = [[entry[1],entry[2]]]

        for key in json_.keys():
            json_[key] = self.merge_intervals(json_[key])
        with open(self.jsonfile, 'w') as f:  f.write(json.dumps(json_,sort_keys=True))

    def merge_intervals(self, intervals):
        out = []
        sorted_intervals = sorted(intervals, key=itemgetter(0))

        for i in intervals:#sorted(intervals, key=lambda i: i.start):
            if out and i[0] <= out[-1][1]+1:
                out[-1][1] = max(out[-1][1], i[1])
            else:
                out += i,
        return out
if __name__ == '__main__':
    cert = Certifier(sys.argv, verbose=False)
    cert.writeQuery()
    cert.writeJSON()                                                                    
