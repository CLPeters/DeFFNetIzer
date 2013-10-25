#    configs.py - A module for cross-platform configuration storage
#    Copyright (C) 2005 by Jonathan Rosebaugh
#    Portions copyright 2004 by Fadly Tabrani; see below for details
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



import os
from ConfigParser import RawConfigParser

class FileConfig(RawConfigParser):
    def __init__(self, path):
        RawConfigParser.__init__(self)
        self.mypath = path
        self.read(self.mypath)
    def write(self):
        RawConfigParser.write(self, open(self.mypath, 'w'))

class RegConfig:
    """ Class that encapsulates a registry (path) as a configuration store.

        section = registry key
        option = registry valuename
        value = registry value

        Storage model = dictionary

    This class is derived from the one listed at
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/335817
    To the best of my knowledge, the original code was licensed under 
    the Python license and is copyright 2004 by Fadly Tabrani.
    """

    def __init__(self, reg_path=None, autowrite=False):
        
        self._regpath = reg_path
        self._autowrite = autowrite
        self._store = {}

        # Autowrite is available only if a registry path is provided.
        if not self._regpath: self._autowrite = False

        # read the registry and store values if path given.
        if self._regpath: self.read(self._regpath)


    def add_section(self, section):
        """ Add a section named section to the instance. If a section by the
            given name already exists, ValueError is raised. """
        if not self.has_section(section):
            self._store[section] = {}
        else:
            raise ValueError("Section already exists")
        
    def get(self, section, option):
        """ Get an option value for the named section. """
        if self.has_option(section, option):
            return self._store[section][option][0]

                
    def _get_default_regkey(self, regpath=None, forwriting=False):
        """ Get the registry key handle for registry operations. provided the
            registry path. """ 
        if regpath:
            key = regpath
            subkey = ''
            
            while os.path.split(key)[0]:
                key, tmp = os.path.split(key)
                subkey = '\\'.join([tmp, subkey])              
            if key == 'HKEY_CLASSES_ROOT':
                key = _winreg.HKEY_CLASSES_ROOT
            elif key == 'HKEY_CURRENT_CONFIG':
                key = _winreg.HKEY_CURRENT_CONFIG
            elif key == 'HKEY_CURRENT_USER':
                key = _winreg.HKEY_CURRENT_USER
            elif key == 'HKEY_DYN_DATA':
                key = _winreg.HKEY_DYN_DATA
            elif key == 'HKEY_LOCAL_MACHINE':
                key = _winreg.HKEY_LOCAL_MACHINE
            elif key == 'HKEY_PERFORMANCE_DATA':
                key = _winreg.HKEY_PERFORMANCE_DATA
            elif key == 'HKEY_USERS':
                key = _winreg.HKEY_USERS
            else:
                raise TypeError('Invalid registry key (HKEY_)')
            if forwriting:
                try:
                    hkey = _winreg.CreateKey(key, subkey)
                except:
                    raise WindowsError('Cannot open registry path')
                else:
                    return hkey
            else:
                try:
                    hkey = _winreg.OpenKey(key, subkey)
                except:
                    try:
                        hkey = _winreg.CreateKey(key, subkey)
                    except:
                        raise WindowsError('Cannot open registry path')
                    else:
                        return hkey
                else:
                    return hkey                    

    def items(self, section):
        """ Return a list of (name, value) pairs for each option in the given
            section. """
        if self.has_section(section):
            sectiondict = self._store[section]
            ret = []
            for option in sectiondict.keys():
                value, type = sectiondict[option]
                ret.append((option, value))
            return ret
        
        
    def has_option(self, section, option):
        """ If the given section exists, and contains the given option. """
        if self._store.has_key(section):
            sectiondict = self._store[section]
            return sectiondict.has_key(option)
    
    
    def has_section(self, section):
        """ Indicates whether the named section is present in the
            configuration. """
        return self._store.has_key(section)
        
        
    def options(self, section):
        """ Returns a list of options available in the specified section. """
        if self._store.has_key(section):
            sectiondict = self._store[section]
            if sectiondict:
                return sectiondict.keys()
            
            
    def read(self, regpath=None):
        """ Can be a single or a list of registry paths. When multiple registry
            keys are read, options and values are overwritten in a FIFO
            fashion ordered from the list. """
        if regpath:
            #try:
                if isinstance(regpath, list):
                    for rp in regpath:
                        self._read(self._get_default_regkey(rp))
                else:
                    self._read(self._get_default_regkey(regpath))
            #except Exception, e:
            #    if not self._autowrite: raise e
                
    def _read(self, regkey=None):
        """ Parses a registry path into sections, options and values. """
        if regkey:
            index = 0
            while 1:
                try:
                    section = _winreg.EnumKey(regkey, index)
                except: 
                    break
                else:
                    try:
                        self.add_section(section)
                    except:
                        pass
                    index += 1
                    
            for section in self.sections():
                index = 0
                while 1:
                    try:
                        hkey = _winreg.OpenKey(regkey, section)   
                        valuename, data, type = _winreg.EnumValue(hkey, index)
                    except:
                        break
                    else:
                        RegConfig.set(self, section, valuename, (data, type), readop=True)
                        index += 1
                        if hkey: _winreg.CloseKey(hkey)
            if regkey: _winreg.CloseKey(regkey)
                        
                        
    def remove_option(self, section, option):
        if self.has_option(section, option):
            del self._store[section][option]
            
                     
    def remove_section(self, section):
        if self.has_section(section):
            del self._store[section]     


    def sections(self):
        """ Return a list of the sections available. """
        return self._store.keys()
    

    def set(self, section, option, value, check=True, readop=False):
        """ If the given section exists, set the given option to the specified
            value; if check=True ValueError is raised if it nonexistent
            otherwise the section is written. """
        if not self.has_section(section):
            if check and not self._autowrite:
                raise ValueError('Section does not exist')
            self.add_section(section)
            
        sectiondict = self._store[section]
        
        if isinstance(value, tuple):
            pass
        else:
            value = self._valueregform(value)
            
        # Automatically write to rgistry if specified.
        if self._autowrite and not readop:
            self._write_reg(self._regpath, section, option, value)
                    
        
        sectiondict[option] = value
        

    def _valueregform(self, value):
        """ Converts values set by the user to a from to be stored in the
            registry. """
        if isinstance(value, str) or isinstance(value, unicode):
            value = (value, _winreg.REG_SZ)
        elif isinstance(value, int):
            value = (value, _winreg.REG_DWORD)
        elif isinstance(value, list):
            for s in value:
                if not isinstance(s, str) or isinstance(s, unicode):
                    raise TypeError(
                        "Values in list must be of type str or unicode.")
            value = (value, _winreg.REG_MULTI_SZ)
        else:
            raise TypeError('Invalid value')
    
        return value
    
    def write(self, regpath=None):
        """ Writes configuration to the registry path. """
        if not regpath:
            regpath = self._regpath
        if regpath:
            for section in self.sections():
                sectiondict = self._store[section]
                for option in sectiondict.keys():
                    apply(self._write_reg, (regpath, section, option,
                                            sectiondict[option]))
        
        
    def _write_reg(self, regpath, section, option, value):
        """ Writes to the registry path. """
        hkey = _winreg.CreateKey(self._get_default_regkey(regpath, True),
                                 section)
        _winreg.SetValueEx(hkey, option, 0, value[1], value[0])
        if hkey: _winreg.CloseKey(hkey)


if os.name == "nt":
    try:
        import _winreg
        class PortConfig(RegConfig):
            def __init__(self, appname="PythonApp", shortappname="pyapp"):
                regpath = "\\".join(["HKEY_CURRENT_USER", "Software", "".join(appname.split())])
                RegConfig.__init__(self, regpath)
                
    except ImportError:
        class PortConfig(FileConfig):
            def __init__(self, appname="PythonApp", shortappname="pyapp"):
                filename = os.path.join(os.environ['HOME'], "."+shortappname)
                FileConfig.__init__(self, filename)

else:
    class PortConfig(FileConfig):
        def __init__(self, appname="PythonApp", shortappname="pyapp"):
            filename = os.path.join(os.environ['HOME'], "."+shortappname)
            FileConfig.__init__(self, filename)



class TheConfig(PortConfig):
    def __init__(self):
        PortConfig.__init__(self, "De-FFNet-izer", "deffnet")
#        PortConfig.__init__(self, "Test", "test")
        if not self.has_section('misc'):
            self.add_section('misc')
    def get(self, option, default=None):
        if self.has_option('misc', option):
            return PortConfig.get(self, 'misc', option)
        else:
            return default
    def set(self, option, value):
        PortConfig.set(self, 'misc', option, value)
    