# Sonarqube-cleaner

Utility to remove old projects in SonarQube.

```
$ python3 clean.py -h
usage: clean.py [-h] [-s SERVER] [-u USER] [-p PASSWORD] [-d DAYS] [-o ORGANIZATION] [-v]

Monitor for HTTP traffic

optional arguments:
  -h, --help            show this help message and exit
  -s SERVER, --server SERVER
                        Sonar URL
  -u USER, --user USER  Admin user to be used to connect
  -p PASSWORD, --password PASSWORD
                        Admin password to be used to connect
  -d DAYS, --days DAYS  Days to leave
  -o ORGANIZATION, --organization ORGANIZATION
                        Organization to remove from
  -v, --verbose         Increase verbosity
```
