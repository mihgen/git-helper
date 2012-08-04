#!/usr/bin/env python
import sys

import argparse
import re

import git_api
import config


class Review(object):

    def __init__(self, params):
        self.git = git_api.GitEngine("local_repo", params.repo_url)
        self.github = None

        p = re.compile('git@github.com:(\S+)\/(\S+)\.git')
        self.user, self.repo = p.match(params.repo_url).groups()

        self.repo_url = params.repo_url
        self.remote_branch = params.remote_branch


    def rebase(self):
        self.git.fetch()

        commits = self.git.diff_commits("remotes/origin/master",
                                   "remotes/origin/%s" % self.remote_branch)
        if not commits:
            print "ERROR: Same or older than master branch!"
            sys.exit(1)
        self.git.checkout_from_remote_branch("remotes/origin/master")
        for sha in commits:
            # Raises exception if it can't be fast-forwarded
            print "Cherry-picking %s" % sha
            self.git.cherry_pick(sha)

    def push(self):
        self.git.push("master")
        # Remove remote branch as we don't need it after merge
        self.git.remove_remote_branch(self.remote_branch)

    def add_pull_request(self, title="default title", body="default body"):
        self._github_lazy_init()
        self.github.create_pull_request(self.user, self.repo, self.user, "master",
                self.remote_branch, title, body)

    def _github_lazy_init(self):
        if not self.github:
            self.github = git_api.GithubEngine(config.GITHUB_USER,
                    config.GITHUB_PASSWORD)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Review system")
    parser.add_argument('--repo', dest='repo_url', type=str, required=True,
            help='URL to repository, format: git@github.com:<user>/<repo>.git')
    parser.add_argument('--branch', dest='remote_branch', type=str,
            required=True, help='Remote branch')
    parser.add_argument('-t' '--pull_title', dest='pull_title', type=str,
            help='Title for pull request')
    parser.add_argument('-b' '--pull_body', dest='pull_body', type=str,
            help='Body for pull request')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--check', action='store_true',
            help='Check if branch can be rebased. Prepare it for tests.')
    group.add_argument('-a', '--add', action='store_true',
            help='Add pull request from user branch to master')
    group.add_argument('-p', '--push', action='store_true',
            help='Pushes rebased code from user branch to remote master')

    params = parser.parse_args()

    rvw = Review(params)

    # Expected flow:
    # 1. --check for attempts to rebase
    # 2. ./run_tests against current code (out of this script)
    # 3. --add  to create pull request on github
    # 4. Someone reviews code on github
    # 5. Release manager runs --push to rebase user branch and push to master

    if params.check:
        rvw.rebase()
    elif params.add:
        rvw.add_pull_request(params.pull_title, params.pull_body)
    elif params.push:
        rvw.rebase()
        rvw.push()

