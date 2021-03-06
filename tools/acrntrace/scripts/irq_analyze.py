#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
This script defines the function to do the irq related analysis
"""

import csv
import struct
from config import TSC_FREQ

TSC_BEGIN = 0
TSC_END = 0

VMEXIT_ENTRY = 0x10000

LIST_EVENTS = {
    'VMEXIT_EXTERNAL_INTERRUPT':   VMEXIT_ENTRY + 0x00000001,
}

IRQ_EXITS = {}

# 4 * 64bit per trace entry
TRCREC = "QQQQ"

def parse_trace(ifile):
    """parse the trace data file
    Args:
        ifile: input trace data file
    Return:
        None
    """

    fd = open(ifile, 'rb')

    while True:
        global TSC_BEGIN, TSC_END
        try:
            line = fd.read(struct.calcsize(TRCREC))
            if not line:
                break
            (tsc, event, vec, d2) = struct.unpack(TRCREC, line)

            event = event & 0xffffffffffff

            if TSC_BEGIN == 0:
               TSC_BEGIN = tsc

            TSC_END = tsc

            for key in LIST_EVENTS.keys():
                if event == LIST_EVENTS.get(key):
                    if vec in IRQ_EXITS.keys():
                        IRQ_EXITS[vec] += 1
                    else:
                        IRQ_EXITS[vec] = 1

        except struct.error:
            sys.exit()

def generate_report(ofile, freq):
    """ generate analysis report
    Args:
        ofile: output report
        freq: TSC frequency of the device trace data from
    Return:
        None
    """
    global TSC_BEGIN, TSC_END

    csv_name = ofile + '.csv'
    try:
        with open(csv_name, 'a') as filep:
            f_csv = csv.writer(filep)

            rt_cycle = TSC_END - TSC_BEGIN
            assert rt_cycle != 0, "Total run time in cycle is 0, \
                                   TSC end %d, TSC begin %d" \
                                   % (TSC_END, TSC_BEGIN)

            rt_sec = float(rt_cycle) / (float(freq) * 1000 * 1000)

            print ("\nVector \t\tCount \tNR_Exit/Sec")
            f_csv.writerow(['Vector', 'NR_Exit', 'NR_Exit/Sec'])
            for e in IRQ_EXITS.keys():
                pct = float(IRQ_EXITS[e]) / rt_sec
                print ("0x%08x \t %d \t%.2f" % (e, IRQ_EXITS[e], pct))
                f_csv.writerow([e, IRQ_EXITS[e], '%.2f' % pct])

    except IOError as err:
        print ("Output File Error: " + str(err))

def analyze_irq(ifile, ofile):
    """do the vm exits analysis
    Args:
        ifile: input trace data file
        ofile: output report file
    Return:
        None
    """

    print("IRQ analysis started... \n\tinput file: %s\n"
          "\toutput file: %s.csv" % (ifile, ofile))

    parse_trace(ifile)
    # save report to the output file
    generate_report(ofile, TSC_FREQ)
