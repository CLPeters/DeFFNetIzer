#    dircopy.py - A module for copying directories
#    Copyright (C) 2005 by Jonathan Rosebaugh
#    Portions copyright 2005 by Stephen Chappell; see below for details
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of version 2 of the GNU General Public License as 
#    published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


# The first four functions in this file are derived from ones at
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/440626
# And were licensed under the Python license.

def copy_file(path):
    '''copy_file(string)

    Import the needed functions.
    Assert that the path is a file.
    Return all file data.'''
    from os.path import basename, isfile
    assert isfile(path)
    return (basename(path), file(path, 'rb', 0).read())

def paste_file(file_object, path):
    '''paste_file(tuple, string)

    Import needed functions.
    Assert that the path is a directory.
    Create all file data.'''
    from os.path import isdir, join
    try:
        assert isdir(path)
    except:
        raise AssertionError, "%s is not a path" % path
    file(join(path, file_object[0]), 'wb', 0).write(file_object[1])
    
def int_copy_dir(path):
    '''int_copy_dir(string)

    Import needed functions.
    Assert that path is a directory.
    Setup a storage area.
    Write all data to the storage area.
    Return the storage area.'''
    from os import listdir
    from os.path import basename, isdir, isfile, join
    try:
        assert isdir(path)
    except:
        raise AssertionError, "%s is not a path" % path
    dir = (basename(path), list())
    for name in listdir(path):
        next_path = join(path, name)
        if isdir(next_path):
            dir[1].append(int_copy_dir(next_path))
        elif isfile(next_path):
            dir[1].append(copy_file(next_path))
        #print dir
    return dir

def int_paste_dir(dir_object, path):
    '''int_paste_dir(tuple, string)

    Import needed functions.
    Assert that the path is a directory.
    Edit the path and create a directory as needed.
    Create all directories and files as needed.'''
    from os import mkdir
    from os.path import isdir, join
    try:
        assert isdir(path)
    except:
        raise AssertionError, "%s is not a path" % path
    if dir_object[0] is not '':
        path = join(path, dir_object[0])
        try:
            mkdir(path)
        except OSError, (errno, strerror):
            if errno is not 17:
                raise
    for object in dir_object[1]:
        if type(object[1]) is list:
            int_paste_dir(object, path)
        else:
            paste_file(object, path)
            
def copy_dir(path, newpath):
    int_paste_dir(int_copy_dir(path), newpath)