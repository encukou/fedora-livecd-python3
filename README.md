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

Requires python3, git, dnf  and repoquery.

Sample output
-------------

```
----- Good -----
foo
bar

----- Bad -----
spam
spam
```

Names of srpms listed under both sections produce at least one binary RPM that has a runtime
requirement matching ".\*python.\*". Packages in the "Good" section also BuildRequire
".\*python3.\*", while packages in "Bad" section don't.
(Not a 100 % approach, but works for the most part.)

Together, "Good" and "Bad" packages are all packages that depend on ".\*python.\*" that
would end up in a system produced by given kickstart.
