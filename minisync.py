#!/usr/local/bin/python
#
# Copyright (c) 2012, Frederic Delbos
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without 
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the Frederic Delbos nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#     without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

from ftplib import FTP
import os, time, commands, shutil, errno


backups = {
    'myservernick': {
        'host': '',     # hostname or ip of the ftp server
        'user': '',     # user login
        'password': '', # user password
        'path':'./'     # path where to store the archives if absent root path will be used
        },
    }

sites = {
    'mysite': {
        'db': '',       # db name
        'user': '',     # db username
        'password': '', # db password
        'dirs': {
            'directory1': '',   # a directory to save
            'directory2': '',   # another directory to save
            }
        },
    }

tmp_dir = '/tmp' # where to store temporary files (make sure you have enought space left)

binaries = {
    'mysqldump': '/usr/local/bin/mysqldump',
    'tar': '/usr/bin/tar'
    }

def main():
    open_connections()
    os.chdir(tmp_dir)
    for site in sites:
        archive = build_archive(site, sites[site])
        upload_archive(archive)
    close_connections()

def open_connections():
    for backup in backups:
        server = backups[backup]
        server['connection'] = FTP(server['host'])
        server['connection'].login(server['user'], server['password'])
        print server['connection'].nlst()

def close_connections():
    for backup in backups:
        server = backups[backup]
        server['connection'].quit()

def upload_archive(name):
    archive = open(name, 'r')
    for backup in backups:
        server = backups[backup]
        server['connection'].storbinary('STOR %s' % name, archive)
    archive.close()

def build_archive(name, info):
    archive_name = '%s_%s' % (name, time.strftime('%Y-%m-%d_%H-%M-%S'))
    if not os.path.exists(archive_name):
        os.makedirs(archive_name)
    extract_database(info, archive_name)
    copy_dirs(info['dirs'], archive_name)
    tarball = make_archive(archive_name)
    shutil.rmtree(archive_name)
    return tarball

def extract_database(info, archive_name):
    cmd = ('%s %s -u %s -p%s > %s/%s.sql' %
           (binaries['mysqldump'], info['db'], info['user'], info['password'], archive_name, info['db']))
    status, output = commands.getstatusoutput(cmd)
    if status != 0:
        raise Exception('Database dump error', 
                        'An invalide return code was returned by ' + binaries['mysqldump'])

def copy_dirs(dirs, archive_name):
    for directory in dirs:
        dest = '%s/%s' % (archive_name, directory)
        try:
            shutil.copytree(dirs[directory], dest)
        except OSError as exception:
            if exception.errno == errno.ENOTDIR:
                shutil.copy(dirs[directory], dest)
            else:
                raise Exception('Copy error', 'Directory ' + dirs[directory] + ' inaccessible')

def make_archive(archive_name):
    cmd = '%s -czf %s.tgz %s' % (binaries['tar'], archive_name, archive_name)
    status, output = commands.getstatusoutput(cmd)
    if status != 0:
        raise Exception('Archive error',
                        'Failed to create archive %s.tgz' % (archive_name))
    return '%s.tgz' % archive_name

if __name__ == "__main__":
    main()
