#!/usr/bin/python3
import argparse
import logging
import os
import subprocess
import tempfile

import dnf

lgr = logging.getLogger(__name__)
lgr.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
lgr.addHandler(ch)

here = os.path.dirname(__file__)
repoopts = ['--repoid', 'rawhide']
repoopts_source = ['--repoid', 'rawhide-source']

def do_run(cmd):
    lgr.debug('Running: ' + ' '.join(cmd))
    return subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE).communicate()

def checkout_ks_repo(do_checkout=True):
    ks_dir = os.path.join(here, 'spin-kickstarts')
    if not do_checkout:
        return ks_dir
    if not os.path.isdir(ks_dir):
        to_run = ['git', 'clone', 'https://git.fedorahosted.org/git/spin-kickstarts.git']
        do_run(to_run)
    else:
        to_run = ['git', '-C', ks_dir, 'pull']
        do_run(to_run)

    return ks_dir

def load_deps_from_ks(ks_dir, ks_name):
    """Get top dependencies from given kickstart in given dir."""
    # we need to do the set difference in the top level, since one kickstart can
    # exclude something from different kickstart
    add, exclude = _load_deps_from_ks(ks_dir, ks_name)
    return add, exclude

def _load_deps_from_ks(ks_dir, ks_name):
    """Get 2-tuple (dependencies to add, dependencies to exclude) - from given ks in given dir."""
    add_deps = set()
    excl_deps = set()
    ks_lines = open(os.path.join(ks_dir, ks_name), 'r').readlines()
    inside_packages = False
    for l in ks_lines:
        line = l.strip()
        if line.startswith('%packages'):
            inside_packages = True
            continue
        elif line.startswith('%end'):
            inside_packages = False
            continue
        elif line.startswith('%include'):
            incl_ks = line.split()[1]
            add, exclude = _load_deps_from_ks(ks_dir, incl_ks)
            add_deps.update(add)
            excl_deps.update(exclude)
            continue
        if inside_packages:
            if not line or line.startswith('#'):
                continue
            comment_start = line.find('#')
            if comment_start != -1:
                line = line[:comment_start]
            if line.startswith('@'):
                add_deps.add(line.strip())
            elif line.startswith('-'):
                excl_deps.add(line[1:])
            else:
                add_deps.add(line.strip())
    return (add_deps, excl_deps)


def resolve(to_add, to_exclude):
    base = dnf.Base()
    base.conf.cachedir = '/tmp'
    base.conf.substitutions['releasever'] = 22
    repo = dnf.repo.Repo('rawhide', '/tmp')
    repo.metalink = 'https://mirrors.fedoraproject.org/metalink?repo=rawhide&arch=x86_64'
    base.repos.add(repo)
    base.fill_sack(load_system_repo=False)
    base.read_comps()

    for d in to_add:
        if d.startswith('@'):
            group = base.comps.group_by_pattern(d[1:])
            base.group_install(group, ['default', 'mandatory'], exclude=to_exclude)
        elif d not in to_exclude:
            base.install(d)
    base.resolve()

    names = set()
    for transaction_item in base.transaction:
        for pkg in transaction_item.installs():
            names.add(pkg.name)
    return list(names)


def get_srpms_for_python_reverse_deps(all_deps):
    """Find srpm names corresponding to rpms in all_deps which have "python" somewhere
    in their requires.

    Returns:
        mapping of srpms to corresponding binary rpms found on livecd
        for example:
            {'foo': 'foo-libs', 'foo-python', ...}
    """
    req_python = {}
    # preserve the order here so that we see the progress during run
    for dep in sorted(all_deps):
        to_run = ['repoquery', '--requires', dep] + repoopts
        stdout, stderr = do_run(to_run)
        if 'python' in stdout.decode('utf-8'):
            to_run = ['repoquery', '--srpm', '--qf', '%{name}', dep] +\
                     repoopts + repoopts_source
            stdout, stderr = do_run(to_run)
            # sometimes this seems to return multiple identical lines
            srpms = stdout.decode('utf-8').splitlines()
            for srpm in srpms:
                req_python.setdefault(srpm, set())
                req_python[srpm].add(dep)
    return req_python


def get_srpms_that_br_python3(srpms):
    # find out if the srpms require "*python3*" for their build - if so, we'll mark them ok
    req_python3 = {}
    # preserve the order here so that we see the progress during run
    for dep in sorted(srpms):
        to_run = ['repoquery', '--archlist=src', '--requires', dep] + repoopts_source
        stdout, stderr = do_run(to_run)
        if 'python3' in stdout.decode('utf-8'):
            req_python3[dep] = srpms[dep]
    return req_python3


def get_good_and_bad_srpms(ks_name=None, ks_path=None):
    if ks_name and ks_path or (ks_name == ks_path == None):
        raise ValueError('Must specify ks_name xor ks_path!')
    if ks_name:
        ks_dir = checkout_ks_repo()
    else:
        ks_dir, ks_name = os.path.split(ks_path)
    top_deps_add, top_deps_exclude = load_deps_from_ks(ks_dir, ks_name)
    lgr.debug('Adding: ' + str(top_deps_add))
    lgr.debug('Excluding: ' + str(top_deps_exclude))

    all_deps = resolve(top_deps_add, top_deps_exclude)
    lgr.debug('All deps: ' + str(sorted(all_deps)))

    srpms_req_python = get_srpms_for_python_reverse_deps(all_deps)
    srpms_req_python3 = get_srpms_that_br_python3(srpms_req_python)

    # remove all the python3-ported rpms from srpms_req_python
    for good in srpms_req_python3:
        srpms_req_python.pop(good)
    return srpms_req_python3, srpms_req_python

def print_srpm(srpm, with_rpms):
    print(srpm[0], end='')
    if with_rpms:
        print(': ' + ' '.join(srpm[1]), end='')
    print()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-k', '--kickstart',
        help='Name of kickstart file from official spin-kickstarts repo.',
        default=None)
    group.add_argument('-p', '--kickstart-by-path',
        help='Absolute/relative path to a kickstart.',
        default=None)
    parser.add_argument('-b', '--binary-rpms',
        help='In addition to SRPMs, also print names of binary RPMs.',
        default=False,
        action='store_true')
    args = parser.parse_args()
    if not args.kickstart and not args.kickstart_by_path:
        args.kickstart = 'fedora-live-workstation.ks'
    good, bad = get_good_and_bad_srpms(ks_name=args.kickstart,
        ks_path=args.kickstart_by_path)

    print('----- Good -----')
    for srpm in sorted(good.items()):
        print_srpm(srpm, with_rpms=args.binary_rpms)

    print()
    print('----- Bad -----')
    for srpm in sorted(bad.items()):
        print_srpm(srpm, with_rpms=args.binary_rpms)
