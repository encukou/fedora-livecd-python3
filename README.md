fedora-livecd-python3
=====================

Script to find out state of Python 3 support on Fedora livecd according to official kickstarts.

Uses kickstarts from https://git.fedorahosted.org/git/spin-kickstarts.git

Note, that even with DNF 0.6.1 this still outputs more packages than there actually are on
livecd, see [rhbz#1131969#c8](https://bugzilla.redhat.com/show_bug.cgi?id=1131969#c8).

dnf-livecd-python.py
--------------------

Usage:

```
./dnf-livecd-python.py (-k KICKSTART | -p KICKSTART_BY_PATH) [-b]
```

You can provide kickstart either by filename of kickstart from Fedora's official spin-kickstarts
repo (`-k`) or you can provide a path to a kickstart on your system (`-p`).

If you want to see a list of binary RPMs depending on Python for every SRPM, use `-b` switch.

Requires python3, git and dnf.

Sample output
-------------

```
----- Good -----
foo
bar

----- Bad -----
spam
```

Names of SRPMs under each section are SRPMs that have at least one python3 (in Good)
or python2 (bad) binary RPM on desired LiveCD. Use `-b` to find out which these binary RPMs are.
A SRPM can end up in both sections if it has both python2 and python3 dependent binary
RPMs on LiveCD.
