#!/usr/bin/env python

import argparse
import atexit
import collections
import contextlib
import csv
import itertools
import operator
import os
import tarfile
import tempfile
import sys
import yaml

from collections import namedtuple
from operator import itemgetter, attrgetter

import pyma.fs
import pyma.log


parser = argparse.ArgumentParser(__doc__)
parser.add_argument('scenario', type=argparse.FileType('r'), help='Path to scenario file.')
parser.add_argument('filenames', nargs='*', metavar='source', help='Path to source file.')
args = parser.parse_args()


scenario = yaml.load(args.scenario)

Record = namedtuple('Record', ('meta', 'row'))

def map(rows):
    for row in rows:
        meta = {name: eval(u'lambda row: {}'.format(code))(row)
            for name, code in scenario.items()
            if name in ('filename', 'column_header', 'row_header')
        }
        if scenario['value'].startswith('sum(1'):
            row = []
        yield Record(meta, row)


groupby = (lambda rows, key: itertools.groupby(sorted(rows, key=key), key=key))


def reduce(records):
    for meta, record_group in groupby(records, key=attrgetter('meta')):
        rows = [record.row for record in record_group]
        value = eval(u'lambda rows: {}'.format(scenario['value']))(rows)
        metric = dict(meta, value=value)
        yield metric


uniq = lambda values: list(collections.OrderedDict.fromkeys(values))
to_int = lambda v: int(v) if isinstance(v, basestring) and v.isdigit() else v
num_sorted = lambda values: sorted(values, key=to_int)


def format(metrics):
    for filename, metric_group in groupby(metrics, key=itemgetter('filename')):
        metric_group = list(metric_group)
        fieldnames = num_sorted(uniq(m['column_header'] for m in metric_group))
        fieldnames.insert(0, scenario['column_header_name'][1:-1])
        rows = []
        for row_header, metric_subgroup in groupby(metric_group, key=itemgetter('row_header')):
            row = {m['column_header']: m['value'] for m in metric_subgroup}
            row[scenario['column_header_name'][1:-1]] = row_header
            rows.append(row)
        yield filename, fieldnames, rows


_is_tarball = lambda filename: (
    filename.endswith('.tar') or
    filename.endswith('.tar.gz') or
    filename.endswith('.tar.bz2')
)


@contextlib.contextmanager
def open_source_files(filepaths):
    tmpdirs = []
    def _delete(paths):
        for path in paths:
            if not os.path.exists(path):
                continue
            pyma.log.info('deleting {}'.format(path))
            pyma.fs.delete(path)
    atexit.register(_delete, tmpdirs)
    def _open_source_files(filepaths):
        if not filepaths:
            yield sys.stdin
            return
        for filepath in filepaths:
            if _is_tarball(filepath):
                tmpdir = tempfile.mkdtemp()
                tmpdirs.append(tmpdir)
                pyma.log.info('extracting {} to {}'.format(filepath, tmpdir))
                archive = tarfile.open(filepath)
                archive.extractall(tmpdir)
                for path, dirnames, filenames in os.walk(tmpdir):
                    for filename in filenames:
                        filepath = os.path.join(path, filename)
                        pyma.log.info('reading {}'.format(filepath))
                        yield open(filepath)
                continue
            pyma.log.info('reading {}'.format(filepath))
            yield open(filepath)
    yield _open_source_files(filepaths)
    _delete(tmpdirs)



def main():
    with open_source_files(args.filenames) as files:
        readers = (csv.DictReader(f, delimiter=';') for f in files)
        reader = itertools.chain.from_iterable(readers)

    metrics = reduce(map(reader))
    filenames = []
    for filename, fieldnames, rows in format(metrics):
        pyma.log.info('writing {}'.format(filename))
        with open(filename, 'w') as fdout:
            writer = csv.DictWriter(fdout, fieldnames=fieldnames,
                delimiter=';', restval=scenario['default'])
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        filenames.append(filename)


if __name__ == '__main__':
    main()

