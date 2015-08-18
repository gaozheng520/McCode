#!/usr/bin/env python
#
#  Implements ui-independent functionality for mcplot-gnuplot.
#
import Gnuplot
import string
import numpy
import re
import os

# base class for mcstas gnuplot objects
class McGnuplotObject():
    def __init__(self, key, data_struct, gp):
        """set key, data for this instance"""
        self.gp = gp
        self.key = key
        self.data = data_struct
        return
    
    def plot(self, log_scale=False):
        """hand data to plot_impl"""
        self.plot_impl(self.gp, self.data, log_scale=log_scale)
    
    @staticmethod
    # override this to support inclusion innnnn overview plots
    def plot_impl(gp, data, log_scale=False):
        """implement gnuplot commands"""
        print('McGnuPlotObject: plot_impl not implemented')
        return

# implements overview plotting (NOTE: overrides plot() rather than plot_impl())
class McGnuplotOverview(McGnuplotObject):
    # set at construction time
    __siblings = None

    def __init__(self, key, gp, siblings):
        McGnuplotOverview.__siblings = siblings
        return McGnuplotObject.__init__(self, key, None, gp)
    
    def plot(self, log_scale=False):
        """plots all files to a singe window as multiplot (individually as array_1d or array_2d)"""
        (nx, ny) = McGnuplotOverview.__calc_panel_size(len(self.__siblings))
        self.gp('set multiplot layout %d,%d rowsfirst' % (ny, nx))
        for sib in self.__siblings:
            sib.plot_impl(self.gp, sib.data, log_scale=log_scale)

    @staticmethod
    def __calc_panel_size(num):
        """given the number of monitors to display as multiplot, return rows/cols"""
        from pylab import sqrt
        Panels = ( [1,1], [2,1], [2,2], [3,2], [3,3], [4,3], [5,3], [4,4],
                   [5,4], [6,4], [5,5], [6,5], [7,5], [6,6], [8,5], [7,6],
                   [9,5], [8,6], [7,7], [9,6], [8,7], [9,7], [8,8], [10,7],
                   [9,8], [11,7], [9,9], [11,8], [10,9], [12,8], [11,9],
                   [10,10] )
        # default size about sqrt($num) x sqrt($num).
        ny = int(sqrt(num))
        nx = int(num/ny)
        if nx*ny < num:
            nx = nx+1;
        
        fit = nx*ny - num
    
        for j in range(0, 31):
            panel = Panels[j]
            d = panel[0]*panel[1] - num
            if d > 0:
                if d < fit:
                    fit = d; nx = panel[0]; ny = panel[1]
        
        return nx, ny

# implements 2d plotting 
class McGnuplotPSD(McGnuplotObject):
    def __init__(self, key, data_struct, gp):
        return McGnuplotObject.__init__(self, key, data_struct, gp)
    
    @staticmethod
    def plot_impl(gp, data, log_scale=False):
        gp("set view map")
        gp.title(data['title'])
        gp.xlabel(data['xlabel'])
        gp.ylabel(data['ylabel'])
        gp("splot '%s' matrix using 1:2:3 index 0 w image notitle" % data['fullpath'])

# implements 1D plotting
class McGnuplot1D(McGnuplotObject):
    def __init__(self, key, data_struct, gp):
        return McGnuplotObject.__init__(self, key, data_struct, gp)
        
    @staticmethod
    def plot_impl(gp, data, log_scale=False):
        plot_data = Gnuplot.Data(data['data'],
                    using='1:2:3',
                    with_='errorbars')
        gp.plot(plot_data,
                title=data['title'], 
                xlabel=data['xlabel'],
                ylabel=data['ylabel'])

# mcgnuplot proxy and constructor
class McGnuplotter():
    __overview_key = '< overview >'

    def __init__(self, input_file, noqt=False):
        """
        constructor - takes a .sim file or a .dat file name (for single vs. multiplot usage)
        """
        gp_persist = 0
        if noqt:
            gp_persist = 1
        
        self.__gnuplot_objs = {}
        
        # check input file type & setup
        file_ext = os.path.splitext(input_file)[1]
        if file_ext == '.sim':
            data_file_lst = get_overview_files(input_file)
            siblings = []
            
            for data_file in data_file_lst:
                data_struct = get_monitor(data_file)
                if re.search('array_2d.*', data_struct['type']):
                    gpo = McGnuplotPSD(data_struct['file'], data_struct, Gnuplot.Gnuplot(persist=gp_persist))
                    siblings.append(gpo)
                else:
                    gpo = McGnuplot1D(data_struct['file'], data_struct, Gnuplot.Gnuplot(persist=gp_persist))
                    siblings.append(gpo)
            
            overview = McGnuplotOverview(McGnuplotter.__overview_key, Gnuplot.Gnuplot(persist=gp_persist), siblings)
            self.__gnuplot_objs[overview.key] = overview
            for gpo in siblings:
                self.__gnuplot_objs[gpo.key] = gpo
            
        elif file_ext == '.dat':
            data_struct = get_monitor(input_file)
            gpo = McGnuplot1D(data_struct['file'], data_struct, Gnuplot.Gnuplot(persist=gp_persist))
            self.__gnuplot_objs[gpo.key] = gpo
        else:
            raise Exception('McGnuPlotter: input file must be .sim or .dat')
    
    def plot(self, key, log_scale=False):
        """
        plots .dat file corresponding to key
        """
        if key in self.__gnuplot_objs:
            self.__gnuplot_objs[key].plot(log_scale)
        else:
            raise Exception('McGnuplotter.plot: no such key')
        
    def get_data_keys(self):
        """
        returns an alpha-num sorted list of all McGnuplotObject instances installed at construction time by key
        """
        return sorted(self.__gnuplot_objs.keys(), key=lambda item: (int(item.partition(' ')[0])
                                                                    if item[0].isdigit() else float('inf'), item))

def get_overview_files(sim_file):
    """
    returns a list of data files associated with the "mccode.sim" file (full paths)
    """
    org_dir = os.getcwd()
    try:
        sim_file = os.path.abspath(sim_file)
        if os.path.dirname(sim_file) != '':
            os.chdir(os.path.dirname(sim_file))
            sim_file = os.path.basename(sim_file)
        
        monitor_files = filter(lambda line: (line.strip()).startswith('filename:'), open(sim_file).readlines())
        monitor_files = map(lambda f: os.path.abspath(f.rstrip('\n').split(':')[1].strip()), monitor_files)
    finally:
        os.chdir(org_dir)
    
    return monitor_files

def get_monitor(mon_file):
    """
    returns monitor .dat file info structured as a python dict
    """
    is_header = lambda line: line.startswith('#')
    header_lines = filter(is_header, open(mon_file).readlines())
    
    file_struct_str ="{"
    for j in range(0, len(header_lines)):
        # Field name and data
        Line = header_lines[j]; Line = Line[2:len(Line)].strip()
        Line = Line.split(':')
        Field = Line[0]
        Value = ""
        Value = string.join(string.join(Line[1:len(Line)], ':').split("'"), '')
        file_struct_str = file_struct_str + "'" + Field + "':'" + Value + "'"
        if j<len(header_lines)-1:
            file_struct_str = file_struct_str + ","
    file_struct_str = file_struct_str + "}"
    file_struct = eval(file_struct_str)
    
    # Add the data block:
    file_struct['data'] = numpy.loadtxt(mon_file)
    file_struct['fullpath'] = mon_file
    file_struct['file'] = os.path.basename(mon_file)
    print("Loading " + mon_file)
    
    return file_struct
