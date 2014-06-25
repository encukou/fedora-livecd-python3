#!/usr/bin/python3

import argparse
import logging
import os
import subprocess

lgr = logging.getLogger(__name__)
lgr.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
lgr.addHandler(ch)

def do_run(cmd):
    lgr.debug('Running: ' + ' '.join(cmd))
    return subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE).communicate()

repoopts = ['--repoid', 'rawhide']
repoopts_source = ['--repoid', 'rawhide-source']
here = os.path.dirname(__file__)

def checkout_ks_repo():
    ks_dir = os.path.join(here, 'spin-kickstarts')
    if not os.path.isdir(ks_dir):
        to_run = ['git', 'clone', 'https://git.fedorahosted.org/git/spin-kickstarts.git']
        do_run(to_run)
    else:
        to_run = ['git', '-C', ks_dir, 'pull']
        do_run(to_run)
    
    return ks_dir

def get_top_deps(ks_dir, ks_name):
    """Get top dependencies from given kickstart in given dir."""
    # we need to do the set difference in the top level, since one kickstart can
    # exclude something from different kickstart
    top, exclude = _get_top_deps(ks_dir, ks_name)
    return top - exclude

def _get_top_deps(ks_dir, ks_name):
    """Get 2-tuple (top dependencies, dependencies to be excluded) - from given ks in given dir."""
    top_deps = set()
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
            add, exclude = _get_top_deps(ks_dir, incl_ks)
            top_deps.update(add)
            excl_deps.update(exclude)
            continue
        if inside_packages:
            if not line or line.startswith('#'):
                continue
            if line.startswith('@'):
                to_run = ['yum', 'group', 'info', line.strip()] + repoopts
                stdout, sdterr = do_run(to_run)
                for depline in stdout.decode('utf-8').splitlines():
                    if depline.startswith('   '): # 3 spaces
                        top_deps.add(depline.strip(' +')) # 3 spaces and 1 more space or '+'
            elif line.startswith('-'):
                excl_deps.add(line[1:])
            else:
                top_deps.add(line.strip())
    return (top_deps, excl_deps)

def get_recursive_deps(top_deps):
    """Get recursive dependencies of deps specified in top_deps iterable."""
    all_deps = set()
    for dep in top_deps:
        to_run = ['repoquery', '--recursive', '--resolve', '--requires', '--qf', '%{name}', dep] +\
            repoopts
        stdout, stderr = do_run(to_run)
        all_deps.update(stdout.decode('utf-8').splitlines())
    # don't forget to add the actual top_deps
    return all_deps | top_deps

def get_srpms_for_python_reverse_deps(all_deps):
    """Find srpm names corresponding to rpms in all_deps which have "python" somewhere
    in their requires."""
    req_python = set()
    for dep in all_deps:
        to_run = ['repoquery', '--requires', dep] + repoopts
        stdout, stderr = do_run(to_run)
        if 'python' in stdout.decode('utf-8'):
            to_run = ['repoquery', '--srpm', '--qf', '%{name}', dep] +\
                     repoopts + repoopts_source
            stdout, stderr = do_run(to_run)
            # sometimes this seems to return multiple identical lines
            req_python.update(stdout.decode('utf-8').splitlines())
    return req_python

def get_srpms_that_br_python3(srpms):
    # find out if the srpms require "*python3*" for their build - if so, we'll mark them ok
    req_python3 = set()
    for dep in srpms:
        to_run = ['repoquery', '--archlist=src', '--requires', dep] + repoopts_source
        stdout, stderr = do_run(to_run)
        if 'python3' in stdout.decode('utf-8'):
            req_python3.add(dep)
    return req_python3

def get_good_and_bad_srpms(ks_name):
    ks_dir = checkout_ks_repo()
    top_deps = get_top_deps(ks_dir, ks_name)
    recursive_deps = get_recursive_deps(top_deps)
    srpms_req_python = get_srpms_for_python_reverse_deps(recursive_deps)
    srpms_req_python3 = get_srpms_that_br_python3(srpms_req_python)
    return srpms_req_python3, srpms_req_python - srpms_req_python3

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--kickstart', default='fedora-live-base.ks')
    args = parser.parse_args()
    good, bad = get_good_and_bad_srpms(args.kickstart)
    print('----- Good -----')
    for pkg in sorted(good):
        print(pkg)

    print('----- Bad -----')
    for pkg in sorted(bad):
        print(pkg)
