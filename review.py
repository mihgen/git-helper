#!/usr/bin/env python
import sys

import argparse

import git_api


def main():
    parser = argparse.ArgumentParser(description="Review system")
    parser.add_argument('--repo', dest='repo_url', type=str, required=True,
            help='URL to repository')
    parser.add_argument('--branch', dest='remote_branch', type=str,
            required=True, help='Remote branch')

    params = parser.parse_args()

    git = git_api.GitEngine("local_repo", params.repo_url)
    git.fetch()
    if not git.is_rebased("remotes/origin/%s" % params.remote_branch, \
            "remotes/origin/master"):
        print "ERROR: Branch %s is not rebased on master." \
              "Use 'git rebase origin/master' from your branch" % params.remote_branch
        sys.exit(1)

    commits = git.diff_commits("remotes/origin/master",
                               "remotes/origin/%s" % params.remote_branch)
    git.checkout_from_remote_branch("remotes/origin/master")
    for sha in commits:
        git.cherry_pick(sha)

if __name__ == "__main__":
    main()
    
