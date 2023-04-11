#!/usr/bin/env python
# -*- coding: utf-8 -*-
##### Import #############################################
from UDFManager import *
import argparse
import numpy as np
import glob
from operator import itemgetter
import os
import platform
import subprocess
import sys

import evaluate_deform.variables as var
###########################################################
# print("This is module!")
###########################################################
def simple_deform():
	read_arg()
	if var.f_average:
		average()
		plot_ave()
	elif var.f_series:
		series()
	else:
		file_listing()
		calc_stress_all()
		save_data()
		plot()
	return


##############
# Read argument 
def read_arg():
	parser = argparse.ArgumentParser(description='Evaluate deformed simulations !')
	parser.add_argument('-f','--func', type=int, help="Functionality of junction point (int).")
	parser.add_argument('-n', '--nu', type=float, help="Strand density of network (float).")
	parser.add_argument('-m', '--mode', help="Mode of deformation; shear or stretch")
	parser.add_argument('-a', '--average', help="Average multi data of different deformation", action='store_true')
	parser.add_argument('-s', '--series', help="Average multi data of different deformation", action='store_true')
	args = parser.parse_args()
	if args.func and args.nu:
		var.func = args.func
		var.nu = args.nu
	else:
		print('\n#####\nfunctionality and/or nu is not specified')
		print('Default value will be used!')
	if args.mode:
		print('deform mode is set to ', args.mode.lower())
		var.simple_def_mode = args.mode.lower()
	else:
		print('\n#####\ndeformation mode is not set!')
		print('according to file name(shear or stretch), evaluation mode  will be set!')
	if args.average:
		var.f_average = True
	elif args.series:
		var.f_series = True
	return
# File Select
def file_listing():
	target = '*_out.udf'
	udf_list = glob.glob(target)
	if udf_list:
		if var.simple_def_mode == '':
			if udf_list[0].split('_')[0].lower() in ['shear', 'stretch']:
				var.simple_def_mode = udf_list[0].split('_')[0]
			else:
				print('\n#####\nfile name is not start from either shear or stretch.\ndefault mode of stretch will be used!')
				var.simple_def_mode = 'stretch'
	else:
		sys.exit('\n#####\nNo effective *_out.udf file in this directory !!\nSomething wrong !!\n')
	if (udf_list[0].split('_')[1] == 'rate') and ('e' in udf_list[0].split('_')[2]):
		tmp = sorted([[i, float(i.split('_')[2])] for i in udf_list], key= itemgetter(1), reverse=True)
		var.sorted_udf = list(np.array(tmp)[:,0])
	else:
		var.sorted_udf = sorted(udf_list, reverse=True)
	return 

############################
# Calculate stress either for shear or stretch deformation
def calc_stress_all():
	var.ss_data = []
	for target in var.sorted_udf:
		print("Readin file = ", target)
		#
		var.ss_data.append(read_and_calc(target))
	return
# Read Data
def read_and_calc(target):
	uobj = UDFManager(target)
	data = []
	#
	uobj.jump(0)
	cell = uobj.get("Structure.Unit_Cell.Cell_Size")
	# area_init = cell[0]*cell[1]
	# z_init = cell[2]
	for i in range(1, uobj.totalRecord()):
		print("Reading Rec.=", i)
		uobj.jump(i)
		if var.simple_def_mode == 'shear':
			stress = uobj.get('Statistics_Data.Stress.Total.Batch_Average.xy')
			strain = uobj.get('Structure.Unit_Cell.Shear_Strain')
		elif var.simple_def_mode == 'stretch':
			cell = uobj.get("Structure.Unit_Cell.Cell_Size")
			stress_list = uobj.get("Statistics_Data.Stress.Total.Batch_Average")
			# if str(target.split("_")[3]) == 'out.udf':
			# 	stress = (cell[0]*cell[1])*(stress_list[2]-(stress_list[0] + stress_list[1])/2.)/area_init
			# 	strain = uobj.get("Structure.Unit_Cell.Cell_Size.c")/z_init
			# else:
			# 	stress = (cell[0]*cell[1])*(stress_list[2]-(stress_list[0] + stress_list[1])/2.)/(cell[0]*cell[1]*cell[2])**(2/3)
			# 	strain = uobj.get("Structure.Unit_Cell.Cell_Size.c")/(cell[0]*cell[1]*cell[2])**(1/3)
			stress = (cell[0]*cell[1])*(stress_list[2]-(stress_list[0] + stress_list[1])/2.)/(cell[0]*cell[1]*cell[2])**(2/3)
			strain = uobj.get("Structure.Unit_Cell.Cell_Size.c")/(cell[0]*cell[1]*cell[2])**(1/3)
		data.append([strain, stress])
	return data

########################################
# 計算結果をターゲットファイル名で保存
def save_data():
	for i, target_udf in enumerate(var.sorted_udf):
		if (len(target_udf.split('_')) > 2) and ('e' in target_udf.split('_')[2]):
			target_rate = str(target_udf.split("_")[2])
			if str(target_udf.split("_")[3]) == 'out.udf':
				target = "SS_rate_" + target_rate + '.dat'
			else:
				target = f"SS_rate_{target_rate:}_{str(target_udf.split('_')[3])}.dat"
		else:
			target = 'SS_' + target_udf.split('.')[0] + '.dat'
		var.ss_data_list.append(target)
		with open(target,'w') as f:
			# f.write('# Strain\tStress\n\n')
			for line in var.ss_data[i]:
				f.write(str(line[0]) + '\t' + str(line[1]) + '\n')
	return

############################
# 結果をプロット
def plot():
	plot_ss()
	if var.simple_def_mode == 'stretch':
		plot_mr()
	return

# 必要なスクリプトを作成
def plot_ss():
	script_content()
	with open(var.plt_file, 'w') as f:
		f.write(var.script)
	#
	if platform.system() == "Windows":
		subprocess.call([var.plt_file], shell=True)
	elif platform.system() == "Linux":
		subprocess.call(['gnuplot ' + var.plt_file], shell=True)
	return

# スクリプトの中身
def script_content():
	var.script = 'set term pngcairo font "Arial,14"\n\n'
	var.script += '#set mono\nset colorsequence classic\n\n'
	for i, filename in enumerate(var.ss_data_list):
		var.script += 'data' + str(i) + ' = "' + filename + '"\n'
	var.script += 'set output "SS_multi.png"\n\n'
	var.script += 'set key left\nset size square\n'
	var.script += 'set xlabel "Strain"\nset ylabel "Stress"\n\n'
	var.script += 'G=' + str(var.nu) + '\nfunc=' + str(var.func) + '\nm=1.5\n'
	if var.simple_def_mode == 'stretch':
		var.script += '#set xrange [1:3]\n#set yrange [0.:]\n#set xtics 0.5\n#set ytics 0.01\n\n'
		var.script += 'p(x)=G*(1.-2./func)*(x-1./x**2.)\n' 
		var.script += 'g(x)=m*p(x)\n\n'
	elif var.simple_def_mode == 'shear':
		var.script += 'set xrange [0:1]\nset yrange [0.:]\n#set xtics 0.5\n#set ytics 0.01\n'
		var.script += 'p(x)=G*(1.-2./func)*x\n\n'
		var.script += 'g(x)=m*p(x)\n\n'
	var.script += 'plot	'
	for i, target in enumerate(var.ss_data_list):
		var.script += 'data' + str(i) + ' w l lw 2 lt ' + str(i+1) + ' ti "rate: ' + (target.split('.')[0]).split('_')[2] + '", \\\n'
	var.script += 'g(x) w l lw 2 lt 6 ti "g=1.5", \\\np(x) w l lw 2 lt 7 ti "Phantom"'
	var.script += '\n\nreset'
	return

##############################
# 
def plot_mr():
	for target in var.ss_data_list:
		plt_file = 'plot_MR_' + target.split('.')[0] + '.plt'
		make_mr_script(plt_file, target)
		#
		if platform.system() == "Windows":
			subprocess.call([plt_file], shell=True)
		elif platform.system() == "Linux":
			subprocess.call(['gnuplot ' + plt_file], shell=True)
	return

# 必要なスクリプトを作成
def make_mr_script(plt_file, target):
	script = script_content2(target)
	with open(plt_file, 'w') as f:
		f.write(script)
	return

# スクリプトの中身
def script_content2(target):
	script = 'set term pngcairo font "Arial,14"\n\n'
	script += '#set mono\nset colorsequence classic\n\n'
	script += 'data = "' + target + '"\n'
	script += 'set output "MR_' + target.split('.')[0] + '.png"\n\n'
	script += 'set key left\nset size square\n'
	script += 'set xrange [0:1]\n#set yrange [0.:0.1]\n#set xtics 0.5\n#set ytics 0.02\n'
	script += 'set xlabel "1/{/Symbol l}"\nset ylabel "{/Symbol s}/({/Symbol l}-1/{/Symbol l}^2)"\n\n'
	script += '## Fit Range\n\nlow = 0.3\nhigh = 0.6\n\n'
	script += 'fit [low:high] a*x+b data usi ( 1/$1 ):( $2/( $1 - 1/( $1**2 ) ) ) via a,b\n\n'
	script += 'set label 1 sprintf("C1 = %.3f", b/2) left at graph 0.2,0.8\n'
	script += 'set label 2 sprintf("C2 = %.3f", a/2) left at graph 0.2,0.7\n'
	script += 'set label 3 sprintf("fit range = %.3f to %.3f", low, high) left at graph 0.2,0.6\n\n#\n'
	script += 'plot data usi ( 1/$1 ):( $2/( $1 - 1/( $1**2 ) ) ) w lp pt 7 lt 1 ti "Original Data", \\\n'
	script += '[low:high] a*x + b w l lw 5 lt 2 ti "Fitted Line"'
	script += '\n\nreset'

	return script

#####
# average
def average():
	dat_list = glob.glob('./*/SS*.dat')
	gathered = []
	for file in dat_list:
		with open(file, 'r') as f:
			for line in f.readlines():
				if line[0] not in ['#', '', '\n']:
					gathered.append(line)
	with open('all.dat', 'w') as f:
		for line in gathered:
			f.write(line)
	return
#####
# plot average
def plot_ave():
	script_ave()
	with open('plot_all.plt', 'w') as f:
		f.write(var.script)
	#
	if platform.system() == "Windows":
		subprocess.call(['plot_all.plt'], shell=True)
	elif platform.system() == "Linux":
		subprocess.call(['gnuplot ' + 'plot_all.plt'], shell=True)
	return

# スクリプトの中身
def script_ave():
	var.script = 'set term pngcairo font "Arial,14"\n\n'
	var.script += '#set mono\nset colorsequence classic\n\n'
	var.script += 'data = "all.dat"\n'
	var.script += 'set output "averaged.png"\n\n'
	var.script += 'set key left\nset size square\n'
	var.script += 'set xlabel "Strain"\nset ylabel "Stress"\n\n'
	var.script += 'G=' + str(var.nu) + '\nfunc=' + str(var.func) + '\nm=1.5\n'
	if var.simple_def_mode == 'stretch':
		var.script += '#set xrange [1:3]\n#set yrange [0.:]\n#set xtics 0.5\n#set ytics 0.01\n\n'
		var.script += 'p(x)=G*(1.-2./func)*(x-1./x**2.)\n' 
		var.script += 'g(x)=m*p(x)\n\n'
	elif var.simple_def_mode == 'shear':
		var.script += '#set xrange [0:1]\nset yrange [0.:]\n#set xtics 0.5\n#set ytics 0.01\n'
		var.script += 'p(x)=G*(1.-2./func)*x\n\n'
		var.script += 'g(x)=m*p(x)\n\n'
	var.script += 'plot	'
	var.script += 'data lc rgb "gray" ti "raw data", \\\n'
	var.script += 'data smooth unique w l lw 2 lt 1 ti "averaged", \\\n'
	var.script += 'g(x) w l lw 2 lt 6 ti "g=1.5", \\\np(x) w l lw 2 lt 7 ti "Phantom"'
	var.script += '\n\nreset'
	return

#####
# Series
def series():
	dir_list = glob.glob('./*/all.dat')
	if platform.system() == "Windows":
		sorted_list = sorted([[os.path.basename(os.path.dirname(x)).replace('_', ' '), x.replace("\\","/"), float(os.path.basename(os.path.dirname(x)).split('_')[1])] for x in dir_list], key=itemgetter(2), reverse=True)
	elif platform.system() == "Linux":
		sorted_list = sorted([[os.path.basename(os.path.dirname(x)).replace('_', ' '), os.path.abspath(x), float(os.path.basename(os.path.dirname(x)).split('_')[1])] for x in dir_list], key=itemgetter(2), reverse=True)
	script_series(sorted_list)
	plot_series()
	return

def plot_series():
	if platform.system() == "Windows":
		subprocess.call(['plot_all.plt'], shell=True)
	elif platform.system() == "Linux":
		subprocess.call(['gnuplot ' + 'plot_all.plt'], shell=True)
	return

# スクリプトの中身
def script_series(sorted_list):
	script = 'set term pngcairo font "Arial,14"\n\n'
	script += '#set mono\nset colorsequence classic\n\n'
	script += 'set output "series.png"\n\n'
	script += 'set key left\nset size square\n'
	script += 'set xlabel "Strain"\nset ylabel "Stress"\n\n'
	script += 'G=' + str(var.nu) + '\nfunc=' + str(var.func) + '\nm=1.5\n'
	if var.simple_def_mode == 'stretch':
		script += 'set xrange [1:2]\n#set yrange [0.:]\n#set xtics 0.5\n#set ytics 0.01\n\n'
		script += 'p(x)=G*(1.-2./func)*(x-1./x**2.)\n' 
		script += 'g(x)=m*p(x)\n\n'
	elif var.simple_def_mode == 'shear':
		script += 'set xrange [0:1]\nset yrange [0.:]\n#set xtics 0.5\n#set ytics 0.01\n'
		script += 'p(x)=G*(1.-2./func)*x\n\n'
		script += 'g(x)=m*p(x)\n\n'
	script += 'plot	'
	for data in sorted_list:
		script += '"' + data[1] + '" smooth unique w l lw 2 ti "' + data[0] + '", \\\n'
	script += 'g(x) w l lw 2 lt 6 ti "g=1.5", \\\np(x) w l lw 2 lt 7 ti "Phantom"'
	script += '\n\nreset'
	#
	with open('plot_all.plt', 'w') as f:
		f.write(script)
	return