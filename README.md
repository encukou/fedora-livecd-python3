fedora-livecd-python3
=====================

Script to find out state of Python 3 support on Fedora livecd according to official kickstarts,
Lorax templates and OSTree manifests

Uses kickstarts from https://git.fedorahosted.org/git/spin-kickstarts.git
Uses Lorax templates from https://git.fedorahosted.org/git/lorax.git
Uses OSTree manifests from https://git.fedorahosted.org/git/fedora-atomic.git

Note, that even with DNF 0.6.1 this still outputs more packages than there actually are on
livecd, see [rhbz#1131969#c8](https://bugzilla.redhat.com/show_bug.cgi?id=1131969#c8).

dnf-livecd-python.py
--------------------

Usage:

```
./dnf-livecd-python.py (-k KICKSTART | -p KICKSTART_BY_PATH | -l LORAX_TEMPLATE | -O OSTREE_MANIFEST )
	[-b] [--actual] [--env-group-optionals]
```

The script measures Python 3 readiness or actuall progress of package set defined by given
kickstart (`-k`), lorax template (`-l`) or ostree manifest (`-o`) from one of the above repos
(kickstart can also be given by path - `-p`).

The script outputs two lists of packages - Good and Bad (see Sample output below).

Without `--actual`, this script measures "readiness", i.e. tries to find out which packages
have already been ported (Good), even though their Python 2 version may still actually be
used; the rest are Bad. With `--actual`, the actual current status is determined - Good
are packages that actually only use Python 3, the rest are Bad.

Good and Bad together are all packages from given kickstart/lorax template/ostree manifest
that depend on Python, PyGTK or PyGobject (both Python 2 and Python 3 versions of these).

If you want to see a list of binary RPMs depending on Python for every SRPM, use `-b` switch.

Requires python3, git, dnf  and repoquery.

Sample output
-------------

Without `-b`:

```
----- Good -----
foo
bar

----- Bad -----
spam
```

With `-b`:

```
----- Good -----
foo: foo-libs foo-python3
bar: barbar

----- Bad -----
spam: python-spam spamgtk
```
