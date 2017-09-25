"""Test accuracy of staleness estimate with idle RS that has a primary."""

# Primary wrote at a random time, up to and including 10 seconds ago, and at
# random intervals <= 10 seconds for the previous minute.
#
# The secondary has replicated up to a random point in the primary's oplog.
#
# The client last checked the primary and secondary at random times up to
# heartbeatFrequencyMS ago.
#
# maxStalenessSeconds is a random number between 0 (in violation of spec) and
# 2 minutes.
#
# Compare actual and estimated staleness, see if the client would correctly
# enforce maxStalenessSeconds for a secondary read, record the outcome.

import argparse
import sys
from collections import OrderedDict

import numpy as np


IDLE_FREQ = 10

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("TRIALS", help="Number of trials",
                        type=int)
    parser.add_argument("OUT", help="CSV filename",
                        type=argparse.FileType('w'))
    return parser.parse_args()


def make_primary_oplog():
    while True:
        # Primary wrote at random intervals up to 10 sec apart.
        # Time began at 0, oplog[0] is the first entry, oplog[-1] the latest.
        oplog = np.cumsum(np.random.rand(100) * IDLE_FREQ)

        # If we generated at least 2 minutes of oplog, return, else try again.
        if oplog[-1] >= 120:
            return oplog


def search(ar, value):
    return np.clip(np.searchsorted(ar, value, side='right') - 1, 0, sys.maxsize)


class ServerDescription:
    def __init__(self, server_type, now, oplog, lag, heartbeat_sec):
        # Last checked up to heartbeat seconds ago.
        ago = np.random.rand() * heartbeat_sec
        self.last_update_time = now - ago
        if server_type == 'primary':
            position = search(oplog, self.last_update_time)
        else:
            position = search(oplog, oplog[-1] - lag - ago)

        self.last_write_date = oplog[position]
        assert self.last_update_time > self.last_write_date


def main(args):
    incorrectly_eligible_case = False
    result_record = OrderedDict([('correct', '%d'),
                                 ('read_pref_valid', '%d'),
                                 ('secondary_eligible', '%d'),
                                 ('primary_last_write_date', '%.2f'),
                                 ('secondary_lag', '%.2f'),
                                 ('secondary_position', '%.2f'),
                                 ('secondary_last_write_date', '%.2f'),
                                 ('primary_desc_last_update_time', '%.2f'),
                                 ('primary_desc_last_write_date', '%.2f'),
                                 ('secondary_desc_last_update_time', '%.2f'),
                                 ('secondary_desc_last_write_date', '%.2f'),
                                 ('heartbeat_sec', '%.2f'),
                                 ('max_staleness_sec', '%.2f')])

    # One more format specifier for "repro".
    result_fmt = ','.join(result_record.values()) + ',"%s"'
    results = []

    for i in range(args.TRIALS):
        # Heartbeat frequency from 500ms to 2 minutes.
        heartbeat_sec = .5 + (np.random.rand() * (120 - .5))
        oplog = make_primary_oplog()
        oplog_len = oplog[-1]

        # Latest write was up to 10 seconds ago.
        now = oplog_len + np.random.rand() * IDLE_FREQ

        # Lag could be as old as the beginning of time (0), but favor small lags
        # to improve test coverage.
        secondary_lag = np.random.power(a=.1) * now

        # Which oplog entry has the secondary replicated to?
        secondary_position = search(oplog, oplog[-1] - secondary_lag)
        secondary_last_write_date = oplog[secondary_position]

        if secondary_position > 0:
            assert oplog[-1] - secondary_last_write_date >= secondary_lag - 0.01

        primary = ServerDescription('primary', now, oplog, secondary_lag,
                                    heartbeat_sec)

        secondary = ServerDescription('secondary', now, oplog, secondary_lag,
                                      heartbeat_sec)

        # maxStalenessSeconds is between 0 (in violation of spec) and 2 minutes.
        max_staleness_sec = np.random.rand() * 120
        read_pref_valid = max_staleness_sec >= (heartbeat_sec + IDLE_FREQ)

        # Estimate secondary_lag, using formula from spec.
        staleness = ((primary.last_write_date - primary.last_update_time) -
                     (secondary.last_write_date - secondary.last_update_time) +
                     heartbeat_sec)

        secondary_eligible = staleness <= max_staleness_sec

        # Is the secondary's lag actually less than maxStalenessSeconds?
        if (oplog[-1] - secondary_last_write_date) <= max_staleness_sec:
            correct = secondary_eligible
        elif secondary_eligible:
            correct = False
            if read_pref_valid:
                # Uh-oh. We selected a secondary that was actually too stale.
                incorrectly_eligible_case = True
        else:
            correct = True

        if correct or not read_pref_valid:
            # Don't record expected outcomes.
            continue

        # Record the outcome.
        r = OrderedDict([
            ('correct', correct),
            ('read_pref_valid', read_pref_valid),
            ('secondary_eligible', secondary_eligible),
            ('primary_last_write_date', oplog[-1]),
            ('secondary_lag', secondary_lag),
            ('secondary_position', secondary_position),
            ('secondary_last_write_date', secondary_last_write_date),
            ('primary_desc_last_update_time', primary.last_update_time),
            ('primary_desc_last_write_date', primary.last_write_date),
            ('secondary_desc_last_update_time', secondary.last_update_time),
            ('secondary_desc_last_write_date', secondary.last_write_date),
            ('heartbeat_sec', heartbeat_sec),
            ('max_staleness_sec', max_staleness_sec)])

        r['repro'] = '%s=%s\0' % (
            ', '.join(result_record),
            ', '.join(str(r[name]) for name in result_record))

        results.append(r)

    if incorrectly_eligible_case:
        print("ERROR: selected a too-stale secondary at least once!")

    results.sort(key=lambda rec: (
        rec['correct'], rec['read_pref_valid'], rec['secondary_eligible']))

    if args.OUT:
        print(args.OUT.name)
        args.OUT.write(','.join(result_record))
        args.OUT.write(',repro')
        args.OUT.write('\n')

        # Reversed.
        for r in results[::-1]:
            line = result_fmt % tuple(r.values())
            args.OUT.write(line)
            args.OUT.write('\n')

    args.OUT.close()
    sys.exit(1 if incorrectly_eligible_case else 0)


if __name__ == '__main__':
    main(parse_args())
