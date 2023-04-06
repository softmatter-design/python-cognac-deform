#!/usr/bin/env python
# -*- coding: utf-8 -*-
##### Import #############################################
# from unittest import result
from UDFManager import *
import argparse
import numpy as np
import glob
import os
import platform
import subprocess
import sys

from scipy.signal import savgol_filter

import evaluate_deform.variables as var
###########################################################
def cyclic_deform():
	read_arg()
	if var.f_average:
		average()
		# plot_ave()
	else:
		file_listing()
		calc_stress_all()
		# post_calc()
		# save_data('SS.dat')
		# plot_ss()
	return

# Read argument 
def read_arg():
	parser = argparse.ArgumentParser(description='Evaluate deformed simulations !')
	parser.add_argument('-f','--func', type=int, help="Functionality of junction point (int).")
	parser.add_argument('-n', '--nu', type=float, help="Strand density of network (float).")
	parser.add_argument('-m', '--mode', help="Mode of deformation; shear or stretch")
	parser.add_argument('-a', '--average', help="Average multi data of different deformation", action='store_true')
	args = parser.parse_args()
	if args.func and args.nu:
		var.func = args.func
		var.nu = args.nu
	else:
		print('\n#####\nfunctionality and/or nu is not specified')
		print('Default value will be used!')
	if args.mode:
		var.cyc_def_mode = args.mode.lower()
	else:
		print('\n#####\ndeformation mode is not set!')
		sys.exit('either mode of shear or stretch should be set!')
	if args.average:
		var.f_average = True
	return

# File Select
def file_listing():
	target = '*_out.udf'
	udf_list = glob.glob(target)
	if udf_list:
		tmp = sorted(udf_list, reverse=True)
		for i in range(int(len(tmp)/2)):
			var.sorted_udf.append(tmp[-2*(i+1):len(tmp)-2*i])
	else:
		sys.exit('\n#####\nNo effective *_out.udf file in this directory !!\nSomething wrong !!\n')
	return 

############################
# Calculate stress either for shear or stretch deformation
def calc_stress_all():
	print(var.sorted_udf)
	for list in var.sorted_udf:
		# tmp_data = []
		for target in list:
			print("Readin file = ", target)
			data_name = target.rsplit('_', 1)[0]
			datalist = read_and_calc(target)
			var.cyc_ss_dic[data_name] = datalist[0]
			save_each_data(data_name+'.dat', datalist)
	return

# Read Data
def read_and_calc(target):
	uobj = UDFManager(target)
	data = []
	#
	if target.split('_')[1] == 'Forward':
		uobj.jump(0)
		cell = uobj.get("Structure.Unit_Cell.Cell_Size")
		area_init = cell[0]*cell[1]
		z_init = cell[2]
	else:
		uobj.jump(1)
		vol = uobj.get("Statistics_Data.Volume.Batch_Average")
		area_init = vol**(2./3.)
		z_init = vol**(1./3.)
	for i in range(1, uobj.totalRecord()):
		print("Reading Rec.=", i)
		uobj.jump(i)
		if var.cyc_def_mode == 'shear':
			stress = uobj.get('Statistics_Data.Stress.Total.Batch_Average.xy')
			tmp_strain = uobj.get('Structure.Unit_Cell.Shear_Strain')
			if tmp_strain >= 0:
				strain = tmp_strain
				if strain > var.cyc_deform_max:
					var.cyc_deform_max = strain
			elif abs(tmp_strain) < 1e-3:
				strain = 0.
			else:
				strain = round(float(var.cyc_deform_max) + tmp_strain, 4)
		elif var.cyc_def_mode == 'stretch':
			cell = uobj.get("Structure.Unit_Cell.Cell_Size")
			stress_list = uobj.get("Statistics_Data.Stress.Total.Batch_Average")
			stress = (cell[0]*cell[1])*(stress_list[2]-(stress_list[0] + stress_list[1])/2.)/area_init
			strain = uobj.get("Structure.Unit_Cell.Cell_Size.c")/z_init

		data.append([str(strain), stress])
	return data

########################################
# 計算結果をターゲットファイル名で保存
def save_each_data(filename, datalist):
	with open(filename, 'w') as f:
		f.write('# Strain\tStress\n\n')
		for line in datalist:
			f.write(str(line[0]) + '\t' + str(line[1]) + '\n')
		f.write('\n\n')
	return

##########################
def average():
	result_dic = {}
	smooth_dic = {}
	accum_f = accum_b = 0.
	for direction in ['Forward', 'Backward']:
		name_dic = {}
		tmp_list = glob.glob('./*/*' + direction + '.dat')
		for file in tmp_list:
			# 下の引数は、No_0_Forward.dat の数字部分：ここでは 0
			name_dic.setdefault(file.rsplit(os.sep, 1)[1].split('_')[1], []).append(file)
		repeat = 0
		for n_repeat in name_dic.keys():
			id = direction + '_' + n_repeat
			data_dic = {}
			for filename in name_dic[n_repeat]:
				with open(filename, 'r') as f:
					for line in f.readlines():
						if line[0] not in ['#', '\n']:
							data_dic.setdefault(line.split()[0], []).append(float(line.split()[1]))
			ave_list = []
			for key in data_dic.keys():
				ave = sum(data_dic[key])/len(data_dic[key])
				ave_list.append([float(key), ave])
			#
			smoothed_list = smooth(direction, ave_list)
			if direction == 'Forward':
				accum_f += integral(smoothed_list)
			else:
				accum_b += integral(smoothed_list)
			#
			result_dic[id] = ave_list
			smooth_dic[id] = smoothed_list

			repeat += 1
	#
	hystloss = (accum_f - accum_b)/ accum_f
	#
	save_seriesdata2('averaged', result_dic)
	save_seriesdata2('smoothed', smooth_dic)

	plot_ss(repeat, hystloss)

	return

def smooth(direction, data):
	smoothed_list = []
	# parameter for savgol_filter
	length = 5
	#
	if direction == 'Forward':
		if var.cyc_def_mode == 'shear':
			data.insert(0, [0.,0.])
		elif var.cyc_def_mode == 'stretch':
			data.insert(0, [1.0,0.])
	dataarray = np.array(data)
	smoothed = savgol_filter(dataarray[:,1], length, 2)
	for i, val in enumerate(smoothed):
		if val > 0:
			smoothed_list.append([data[i][0], val])
		else:
			smoothed_list.append([data[i][0], 0.])
	return smoothed_list

def integral(func):
	accum = 0.
	for x in range(len(func)-1):
		accum += (func[x][1] + func[x+1][1])*abs(func[x+1][0] - func[x][0])/2.
	return accum

########################################
# 計算結果をターゲットファイル名で保存
def save_seriesdata(name, result_dic):
	repeat = int(len(result_dic.keys())/2)
	for i in range(repeat):
		all = result_dic['Forward_' + str(i)] + result_dic['Backward_' + str(i)]
		with open(name + f'_No_{i:}.dat', 'w') as f:
			for line in all:
				f.write(str(line[0]) + '\t' + str(line[1]) + '\n')
	return

def save_seriesdata2(name, result_dic):
	repeat = int(len(result_dic.keys())/2)
	with open(name + '.dat', 'w') as f:
		for i in range(repeat):
			f.write(f'# {i:}\n\n')
			all = result_dic['Forward_' + str(i)] + result_dic['Backward_' + str(i)]
			for line in all:
				f.write(str(line[0]) + '\t' + str(line[1]) + '\n')
			f.write('\n\n')
	return

############################
# 結果をプロット
def plot_ss(repeat, hystloss):
	script_content(repeat, hystloss)
	with open('plot_ss.plt', 'w') as f:
		f.write(var.script)
	#
	if platform.system() == "Windows":
		subprocess.call(['plot_ss.plt'], shell=True)
	elif platform.system() == "Linux":
		subprocess.call(['gnuplot ' + 'plot_ss.plt'], shell=True)
	return

# スクリプトの中身
def script_content(repeat, hystloss):
	var.script = 'set term pngcairo font "Arial,14"\n\n'
	var.script += '#set mono\nset colorsequence classic\n\n'
	var.script += 'data = "averaged.dat"\n'
	var.script += 'set output "CyclicDeform.png"\n\n'
	var.script += 'set key left\nset size square\n'
	var.script += '#set xrange [1:3]\nset yrange [0.:]\n#set xtics 0.5\n#set ytics 0.01\n'
	var.script += 'set xlabel "Strain"\nset ylabel "Stress"\n\n'
	var.script += 'G=' + str(var.nu) + '\nfunc=' + str(var.func) + '\n'
	if var.cyc_def_mode == 'stretch':
		var.script += 'a(x)=G*(x-1./x**2.)\n'
		var.script += 'p(x)=G*(1.-2./func)*(x-1./x**2.)\n\n' 
	elif var.cyc_def_mode == 'shear':
		var.script += 'a(x)=G*x\n'
		var.script += 'p(x)=G*(1.-2./func)*x\n\n'
	var.script += 'plot '
	for i in range(repeat):
		var.script += 'data ind ' + str(i) + ' w l lw 2 lt ' + str(i+1) + ' ti "#' + str(i) + '", \\\n'
	var.script += 'a(x) w l lw 2 lt 10 ti "Affin", \\\np(x) w l lw 2 lt 12 ti "Phantom"'
	var.script += '\n\nreset\n\n'
	#
	var.script += 'set term pngcairo font "Arial,14"\n\n'
	var.script += '#set mono\nset colorsequence classic\n\n'
	var.script += 'data = "smoothed.dat"\n'
	var.script += 'set output "Smoothed.png"\n\n'
	var.script += 'set key left\nset size square\n'
	var.script += '#set xrange [1:3]\nset yrange [0.:]\n#set xtics 0.5\n#set ytics 0.01\n'
	var.script += 'set xlabel "Strain"\nset ylabel "Stress"\n\n'
	var.script += 'G=' + str(var.nu) + '\nfunc=' + str(var.func) + '\n'
	if var.cyc_def_mode == 'stretch':
		var.script += 'a(x)=G*(x-1./x**2.)\n'
		var.script += 'p(x)=G*(1.-2./func)*(x-1./x**2.)\n\n' 
	elif var.cyc_def_mode == 'shear':
		var.script += 'a(x)=G*x\n'
		var.script += 'p(x)=G*(1.-2./func)*x\n\n'
	var.script += f'set label 1 sprintf("Hyst. Loss Ratio = %.2f", {hystloss:}) at graph 0.1, 0.65\n\n'
	var.script += 'plot '
	for i in range(repeat):
		var.script += 'data ind ' + str(i) + ' w l lw 2 lt ' + str(i+1) + ' ti "#' + str(i) + '", \\\n'
	var.script += 'a(x) w l lw 2 lt 10 ti "Affin", \\\np(x) w l lw 2 lt 12 ti "Phantom"'
	var.script += '\n\nreset\n\n'

	return












