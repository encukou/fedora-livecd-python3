fedora-livecd-python3
=====================

Script to find out state of Python 3 support on Fedora livecd according to official kickstarts

Uses kickstarts from https://git.fedorahosted.org/git/spin-kickstarts.git

Usage:

```
./livecd-python.py [-k fedora-live-workstation.ks]
```

Requires git, yum, repoquery and python3.
Sample output:

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
