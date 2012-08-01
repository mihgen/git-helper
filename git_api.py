#!/usr/bin/env python

import subprocess
import sys
import os

import config


class GitEngine(object):

    def __init__(self, local_repo=config.REPO_DIR, repo_url=config.REPO_URL):
        self.local_repo = local_repo
        self.remote_path = repo_url
        self.local_branch = "temp-for-engine"
        try:
            # Raises exception if can't change dir or can't get git info
            self.__exec("git status")
        except:
            # Let's create repo dir and initialize repo.
            self.__exec("mkdir %s" % local_repo, ".")
            self.__exec("git init")

    def __exec(self, command, cwd=None):
        if not cwd:
            cwd = self.local_repo
        print "Executing command %s in cwd=%s" % (command, cwd)
        proc = subprocess.Popen(command, cwd=cwd, \
                     stderr=subprocess.PIPE, \
                     stdout=subprocess.PIPE, \
                     shell=True)
        try:
            stdout_value = proc.stdout.read().rstrip()
            stderr_value = proc.stderr.read().rstrip()
            status = proc.wait()
        finally:
            proc.stdout.close()
            proc.stderr.close()

        if status != 0:
            print "ERRRO: Command: '%s' Status: %s err: '%s' out: '%s'" % \
                    (command, status, stderr_value, stdout_value)
            raise GitEngineError(status, stderr_value)

        return stdout_value

    def push(self, remote_branch, remote_path=None, local_branch=None):
        if not local_branch:
            local_branch = self.local_branch
        if not remote_path:
            remote_path = self.remote_path
        command = "git push %s %s:%s" % \
                (remote_path, local_branch, remote_branch)
        try:
            self.__exec(command)
        except GitEngineError as e:
            if e.status == 1:
                print "ERROR: Not able to push. " \
                      "Possible reason: Branch %s was not rebased to %s." % \
                      (local_branch, remote_branch)
            raise

    def fetch(self, remote_path=None, refs_name="origin"):
        if not remote_path:
            remote_path = self.remote_path
        command = "git fetch " + remote_path
        # add refs definition
        command += " +refs/heads/*:refs/remotes/%s/*" % refs_name
        self.__exec(command)

    def cherry_pick(self, from_sha):
        command = "git cherry-pick %s" % from_sha

        self.__exec(command)

    def diff_commits(self, master_branch, slave_branch):
        """ return ordered (from older to newer) list of sha's"""
        command = "git log %s..%s" % (master_branch, slave_branch)
        command += " --pretty=format:%H"

        out = self.__exec(command)
        # if commits aren't found
        if out == "":
            return []
        # split commit shas to list
        commits = [line for line in out.split("\n")]
        return commits[::-1]

    def checkout_from_remote_branch(self, remote_branch, local_branch=None):
        command = "git checkout %s" % remote_branch
        if not local_branch:
            local_branch = self.local_branch
        else:
            # Store local_branch, we may need it later
            self.local_branch = local_branch
        command += " -b " + local_branch

        # Make sure we overwrite existing branch
        try:
            # Detaching HEAD to be able to remove branch we are currently on
            self.__exec("git checkout %s" % remote_branch)
            # Deleting branch
            self.__exec("git branch -D %s" % local_branch)
        except:
            # Exception is raised if there is no branch to delete
            pass
        self.__exec(command)


class GitEngineError(Exception):

    def __init__(self, status, error):
        self.status = status
        self.error = error

    def __str__(self):
        return repr(self.status + " " + self.error)
