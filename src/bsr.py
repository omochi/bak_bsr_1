#!/usr/bin/env python
# coding: utf-8

import sys
from subprocess import check_output
from subprocess import check_call
from subprocess import CalledProcessError
import random
import re
import os

def shell_mkdir_p(path, dotkeep=False):
  if os.path.isdir(path):
    return
  os.makedirs(path)
  if dotkeep:
    shell_touch(path + '/.keep')

def shell_touch(path, times=None):
  with open(path, 'a'):
    os.utime(path, times)

def shell_is_executable(path):
  return os.path.exists(path) and os.access(path, os.X_OK)

class App:
  __repo_dir = None

  def get_repo_dir(self):
    if self.__repo_dir == None:
      ret = check_output(['git', 'rev-parse', '--show-toplevel'])
      ret = ret.rstrip()
      self.__repo_dir = ret
    return self.__repo_dir

  def get_bsr_dir(self):
    return self.get_repo_dir() + '/.bsr'

  def get_hook_pre_push_dir(self):
    return self.get_bsr_dir() + '/hook/pre_push'

  def get_hook_post_checkout_dir(self):
    return self.get_bsr_dir() + '/hook/post_checkout'

  def make_temp_branch_name(self):
    chars = 'abcdefghijklmnopqrstuvwxyz'
    suf = "".join([random.choice(chars) for x in xrange(8)])
    return 'bsr/temp/' + suf

  def get_version_tag_name(self, version):
    return 'bsr/vers/v' + str(version)

  def check_repo_clean(self):
    ret = check_output(['git', 'status', '--short'])
    ret = ret.rstrip()
    if ret != '':
      raise Exception('repository is dirty')

  def get_versions(self):
    regex = re.compile(r'bsr/vers/v(\d+)')
    ret = check_output(['git', 'tag', '-l'])
    vers = []
    for line in ret.splitlines():
      match = regex.search(line)
      if not match:
        continue
      vers.append(int(match.group(1)))
    vers = sorted(vers, reverse=True)
    return vers

  def get_remote_versions(self):
    regex = re.compile(r'refs/tags/bsr/vers/v(\d+)')
    ret = check_output(['git', 'ls-remote', '-q', '--tags'])
    vers = []
    for line in ret.splitlines():
      match = regex.search(line)
      if not match:
        continue
      vers.append(int(match.group(1)))
    vers = sorted(vers, reverse=True)
    return vers

  def get_version(self):
    regex = re.compile(r'tag: bsr/vers/v(\d+)')
    ret = check_output(['git', 'log', '--oneline', '--decorate'])
    vers = []
    for line in ret.splitlines():
      match = regex.search(line)
      if not match:
        continue
      vers.append(int(match.group(1)))
    if len(vers) == 0:
      raise Exception('get version failed')
    return max(vers)

  def get_latest_version(self):
    vers = self.get_versions()
    if len(vers) == 0:
      return None
    return max(vers)

  def commit_all(self, message):
    check_output(['git', 'add', '--all'])
    check_output(['git', 'commit', '--allow-empty', '-m', message])

  def delete_version(self, version):
    tag = self.get_version_tag_name(version)
    check_output(['git', 'tag', '-d', tag])

  def sync_with_remote(self):
    check_output(['git', 'fetch', '--tags'])
    remote_vers = self.get_remote_versions()
    for ver in self.get_versions():
      if ver not in remote_vers:
        self.delete_version(ver)

  def checkout_version(self, version):
    tag = self.get_version_tag_name(version)
    check_output(['git', 'checkout', '-q', tag])

  def push_new_version(self, version):
    tag = self.get_version_tag_name(version)
    check_output(['git', 'tag', tag])
    try:
      check_output(['git', 'push', 'origin', tag])
    except:
      self.delete_version(version)
      raise
    self.checkout_version(version)

  def run_hooks_in_dir(self, dir):
    os.chdir(dir)
    os.environ['BSR_REPO_DIR'] = self.get_repo_dir()

    files = os.listdir(dir)
    files = sorted(files)
    for file in files:
      if file.startswith('.'):
        continue
      path = dir + '/' + file
      if not shell_is_executable(path):
        continue
      check_call([path])

  def main(self, args):
    if len(args) < 2:
      raise Exception('command not specified')

    command = args[1]
    method_name = 'main_' + command
    method = getattr(self, method_name, None)
    if not method:
      raise Exception('command {0} does not exists'.format(command))
    method(args[2:])

  def main_init(self, args):
    shell_mkdir_p(self.get_hook_pre_push_dir(), dotkeep=True)
    shell_mkdir_p(self.get_hook_post_checkout_dir(), dotkeep=True)

    self.commit_all('bsr init')
    check_output(['git', 'push', 'origin', 'master'])
    self.push_new_version(0)

  def main_checkout(self, args):
    self.check_repo_clean()
    self.sync_with_remote()

    version = None
    if len(args) < 1:
      version = self.get_latest_version()
      if version == None:
        raise Exception('version is not found')
    else:
      version = int(args[0])

    self.checkout_version(version)

    self.run_hooks_in_dir(self.get_hook_post_checkout_dir())

  def main_versions(self, args):
    self.sync_with_remote()
    vers = self.get_versions()
    for ver in vers:
      check_call(['git', 'log', '--decorate', self.get_version_tag_name(ver)])

  def main_push(self, args):
    self.sync_with_remote()
    self.run_hooks_in_dir(self.get_hook_pre_push_dir())

    old_version = self.get_version()
    new_version = old_version + 1
    tag = self.get_version_tag_name(new_version)
    temp_branch = self.make_temp_branch_name()

    message = 'version ' + str(new_version)
    self.commit_all(message)
    check_output(['git', 'checkout', '--orphan', temp_branch])
    self.commit_all(message)
    try:
      self.push_new_version(new_version)
    except:
      # rollback
      check_output(['git', 'reset', self.get_version_tag_name(old_version)])
      self.checkout_version(old_version)
    finally:
      check_output(['git', 'branch', '-D', temp_branch])

  def main_delete(self, args):
    self.sync_with_remote()

    delete_version = None
    if len(args) < 1:
      raise Exception('version not specified')
    delete_version = int(args[0])

    vers = self.get_versions()
    if delete_version >= max(vers):
      raise Exception('latest version can not be deleted')

    for ver in vers:
      if ver <= delete_version:
        check_output(['git', 'push', '--delete', 'origin', self.get_version_tag_name(ver)])

    self.sync_with_remote()


app = App()
app.main(sys.argv)