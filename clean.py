#!/usr/bin/env python
import urllib
import requests
import datetime
import argparse
import logging

logger = logging.getLogger(__name__)


class Sonar: 
    def __init__(self, url):
        self.url = url
        self.session = requests.session()

    def _post(self, path, params=None, data=None):
        headers = {}
        r = self.session.post("%s%s" % (self.url, path), params=params, data=data, headers=headers)
        r.raise_for_status()
        if 'XSRF-TOKEN' in r.cookies:
            self.session.headers['X-XSRF-TOKEN'] = r.cookies['XSRF-TOKEN']
        return r

    def _get(self, path, params):
        r = self.session.get("%s%s" % (self.url, path), params=params)
        r.raise_for_status()
        if 'XSRF-TOKEN' in r.cookies:
            self.session.headers['X-XSRF-TOKEN'] = r.cookies['XSRF-TOKEN']
        return r

    def login(self, login, password):
        r = self._post('/api/authentication/login', params=dict(login=login, password=password))
        logger.info("Login success")
    
    def logout(self):
        self._post('/api/authentication/logout')
        logger.info("Logout success")
    
    def get_projects(self, organization, analyzedBefore=None, ps=None, qualifiers=None):
        params = dict(
            organization=organization,
        )
        if analyzedBefore is not None:
            params['analyzedBefore'] = analyzedBefore
        if ps is not None:
            params['ps'] = ps
        if qualifiers is not None:
            params['qualifiers'] = qualifiers

        next_page = 0
        while True:
            next_page += 1
            params['p'] = next_page
            r = self._get('/api/projects/search', params=params)
            j = r.json()
            for p in j['components']:
                yield p
            if j['paging']['pageIndex'] * j['paging']['pageSize'] >= j['paging']['total']:
                break
        
    def bulk_delete(self, organization, projects):
        data = dict(organization=organization, projects=','.join(projects))
        self._post('/api/projects/bulk_delete', data=data)
         
    def delete(self, organization, project):
        return self.bulk_delete(organization, [project])
       
def configure_logging(verbosity):
    msg_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    VERBOSITIES = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    VERBOSITIES_names = ["ERROR", "WARNING", "INFO", "DEBUG"]
    pos = min(int(verbosity), len(VERBOSITIES) - 1)
    level = VERBOSITIES[pos]
    formatter = logging.Formatter(msg_format)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.info("Logger mode: %s" % VERBOSITIES_names[pos])


def parse_args():
    parser = argparse.ArgumentParser(description="Monitor for HTTP traffic")
    parser.add_argument(
        "-s", "--server", default="http://localhost", help="Sonar URL"
    )
    parser.add_argument(
        "-u", "--user", help="Admin user to be used to connect"
    )
    parser.add_argument(
        "-p", "--password", help="Admin password to be used to connect"
    )
    parser.add_argument(
        "-d", "--days", default=60, help="Days to leave"
    )
    parser.add_argument(
        "-o", "--organization", default="default-organization", help="Organization to remove from"
    )
    
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    configure_logging(args.verbose)

    sonar = Sonar(args.server)
    try:
        sonar.login(args.user, args.password)
        d = datetime.datetime.utcnow() - datetime.timedelta(days=args.days)
        d_str = d.strftime("%Y-%m-%dT%H:%M:%S+0000")
        logger.info("retrieving projects")
        projects = sonar.get_projects(analyzedBefore=d_str, organization=args.organization, ps="500", qualifiers="TRK")
        project_keys = [p['key'] for p in projects]
        logger.info("%s projects found" % len(project_keys))
        while project_keys:
            to_delete = project_keys[:100]
            project_keys = project_keys[100:]
            logger.info("Removing %s projects. %s left" % (len(to_delete), len(project_keys)))
            sonar.bulk_delete(args.organization, to_delete)
    finally:
        sonar.logout()

if __name__ == "__main__":
    main()
