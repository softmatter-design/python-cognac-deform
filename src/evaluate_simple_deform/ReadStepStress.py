#!/usr/bin/env python
# -*- coding: utf-8 -*-
##### Import #############################################
from UDFManager import *
import sys
import os
import shutil
import math
import cmath
import numpy as np
import glob
import platform
import subprocess
import scipy.signal as signal
###########################################################
def calc_step(mode):
	t_udf = file_select_one()
	stress_step, strain_step, gt_step = read_step_stress(t_udf, mode)
	return stress_step, strain_step, gt_step

#----- File Select: Select latest udf data
def file_select_one():
	out_list = glob.glob('Step_*_out.udf')
	time = 0
	for udf in out_list:
		mtime = os.stat(udf).st_mtime
		if mtime > time:
			time = mtime
			latest_udf = udf
	return latest_udf

#----- Read Step Stress data
def read_step_stress(t_udf, mode):
	# low = 1e-5
	print("Readin file = ", t_udf)
	area_init, z_init = calc_init(t_udf)
	uobj = UDFManager(t_udf)
	time = []
	strain = []
	stress = []
	gt = []
	temp = []
	# データ読み込み
	prev_stress = 0.
	for rec in range(uobj.totalRecord()):
		print("Reading Rec.=", rec)
		uobj.jump(rec)
		#
		time.append(uobj.get("Time"))
		#
		if mode == 'elong':
			tmp_strain = uobj.get("Structure.Unit_Cell.Cell_Size.c")/z_init - 1.
		elif mode == 'shear':
			tmp_strain = uobj.get('Structure.Unit_Cell.Shear_Strain')
		strain.append(tmp_strain)
		#
		if rec == 0:
			tmp_stress = 0.
			temp.append(1.)
			stress.append(0.)
			gt.append(0.)
		else:
			temp.append(uobj.get('Statistics_Data.Temperature.Batch_Average'))
			if mode == 'elong':
				stress_list = uobj.get("Statistics_Data.Stress.Total.Batch_Average")
				tmp_stress = stress_list[2]-(stress_list[0] + stress_list[1])/2.
				if tmp_stress <= prev_stress:
					tmp_stress = prev_stress
				tmp_gt = tmp_stress/tmp_strain/3.
			elif mode == 'shear':
				tmp_stress = uobj.get('Statistics_Data.Stress.Total.Batch_Average.xy') #- self.ave_xy
				if tmp_stress <= prev_stress:
					tmp_stress = prev_stress
				tmp_gt = tmp_stress/tmp_strain
			stress.append(tmp_stress)
			gt.append(tmp_gt)
		#
		prev_stress = tmp_stress
	#
	stress_step = np.stack([time, stress, temp], 1)
	strain_step = np.stack([time, strain, temp], 1)
	gt_step = np.stack([time, gt, temp], 1)
	ss = np.stack([strain, stress, temp], 1)
	#
	plot_all(strain_step, 'strain_step.dat')
	plot_all(stress_step, 'stress_step.dat')
	plot_all(gt_step, 'gt_step.dat')
	plot_all(ss, 'ss.dat')
	#
	return stress_step, strain_step, gt_step

#----- Calculate Initial State
def calc_init(target):
	uobj = UDFManager(target)
	uobj.jump(0)
	#
	cell = uobj.get("Structure.Unit_Cell.Cell_Size")
	area_init = cell[0]*cell[1]
	z_init = cell[2]
	#
	uobj.jump(1)
	vol = uobj.get("Statistics_Data.Volume.Batch_Average")
	#
	return area_init, z_init




#########################################################################
# 緩和計算時の応力緩和を計算
def calc_quench(stress_step, strain_step, gt_step, mode):
	c_strain = strain_step[-1][1]
	t_udf_list = file_select()
	stress_quench, strain_quench, gt_quench = read_quench(t_udf_list, c_strain, mode)
	#
	stress_all = make_series(stress_step, stress_quench)
	strain_all = make_series(strain_step, strain_quench)
	gt_all = make_series(gt_step, gt_quench)
	#
	plot_all(stress_all, 'stress_all.dat')
	plot_all(strain_all, 'strain_all.dat')
	plot_all(gt_all, 'gt_all.dat')
	#
	return

#----- File Select
def file_select():
	tmp = []
	udf_list = glob.glob('Quench*_out.udf')
	for i in udf_list:
		val = float(i.split("_")[2])
		tmp.append([val, i])
	tt = sorted(tmp)
	sorted_list = []
	for j in tt:
		sorted_list.append(j[1])
	return sorted_list

#-----
def read_quench(t_udf_list, c_strain, mode):
	stress_quench = []
	strain_quench = []
	gt_quench = []
	for target in t_udf_list:
		print("Readin file = ", target)
		stress_part, strain_part, gt_part = read_and_calc(target, c_strain, mode)
		stress_quench.append(stress_part)
		strain_quench.append(strain_part)
		gt_quench.append(gt_part)
	return stress_quench, strain_quench, gt_quench

#----- Read Data
def read_and_calc(target, c_strain, mode):
	# low = 1e-5
	uobj = UDFManager(target)
	time = []
	temp = []
	stress = []
	strain = []
	gt = []
	# データ読み込み
	prev_stress = 0.
	for i in range(1, uobj.totalRecord()):
		print("Reading Rec.=", i)
		uobj.jump(i)
		#
		time.append(uobj.get("Time"))
		temp.append(uobj.get('Statistics_Data.Temperature.Batch_Average'))
		#
		if mode == 'elong':
			strs = uobj.get("Statistics_Data.Stress.Total.Batch_Average")
			tmp_stress = strs[2]-(strs[0] + strs[1])/2.
			if tmp_stress <= 0.05*prev_stress:
				tmp_stress = 4*prev_stress/5
			if tmp_stress < 1e-4:
				tmp_stress = 1e-4
			tmp_gt = tmp_stress/c_strain/3.
		elif mode == 'shear':
			tmp_stress = uobj.get('Statistics_Data.Stress.Total.Batch_Average.xy') #- self.ave_xy
			if tmp_stress <= 0.05*prev_stress:
				tmp_stress = 4*prev_stress/5
			if tmp_stress < 1e-4:
				tmp_stress = 1e-4
			tmp_gt = tmp_stress/c_strain
			# tmp_stress = low
		#
		stress.append(tmp_stress)
		strain.append(c_strain)
		gt.append(tmp_gt)

		prev_stress = tmp_stress
	#
	mod_stress = signal.savgol_filter(stress, 5, 3)

	stress_part = np.stack([time, mod_stress, temp], 1)
	strain_part = np.stack([time, strain, temp], 1)
	gt_part = np.stack([time, gt, temp], 1)
	return stress_part, strain_part, gt_part

#-----
def make_series(data_step, data_t):
	prev_part = data_t.pop(0)
	for data_part in data_t:
		tmp = []
		i = j = 0
		while i < len(data_part):
			while j < len(prev_part):
				p_time = prev_part[j][0]
				t_time = data_part[i][0]
				if t_time > p_time and j < len(prev_part):
					tmp.append(list(prev_part[j]))
					j += 1
				elif t_time == p_time and j < len(prev_part):
					ave = list([t_time, (data_part[i][1] + prev_part[j][1])/2, (data_part[i][2] + prev_part[j][2])/2])
					tmp.append(ave)
					i += 1
					j += 1
			tmp.append(list(data_part[i]))
			i += 1
		prev_part = tmp
	#
	prev_time = data_step[-1][0]
	mod_part = np.hstack([np.array(prev_part)[:, :1] + prev_time, np.array(prev_part)[:, 1:]])
	data_all = np.vstack([np.array(data_step), mod_part])
	#
	return data_all


###############################################
# 平均値を計算
def average():
	# target = 'stress' #, 'strain'
	dat_list = glob.glob('**/gt_all.dat', recursive = True)
	# print(dat_list)
	list_x = []
	list_y = []
	list_z = []
	for i in dat_list:
		axis = i.split("_")[1]
		if axis == 'x':
			list_x.append(["x", i])
		elif axis == 'y':
			list_y.append(["y", i])
		elif axis == 'z':
			list_z.append(["z", i])
	#
	all_list = []
	multi_list = []
	file_names = []
	for axis_dat in [list_x, list_y, list_z]:
		ax_dat_list = []
		for dat in axis_dat:
			with open(dat[1], 'r') as f:
				tmp = []
				time = []
				for line in f.readlines():
					time.append(float(line.split('\t')[0]))
					tmp.append(float(line.split('\t')[1]))
				ax_dat_list.append(tmp)
				all_list.append(tmp)
		ax_ave = np.average(np.array(ax_dat_list), axis = 0)
		# print(len(ax_ave))
		res_axis = np.stack([time, ax_ave], 1)
		multi_list.append([dat[0], res_axis])
		file_name = 'ave_'+ dat[0] + '_gt.dat'
		save_data(res_axis, file_name)
		#
		file_names.append(file_name)
	#
	ave_all = np.average(np.array(all_list), axis = 0)
	gt_ave_all = np.stack([time, ave_all], 1)
	plot_all(gt_ave_all, 'ave_all_gt.dat')
	#
	shutil.copyfile('./rotate_x_0/strain_all.dat', './strain_all.dat')
	plot('strain_all.dat')
	#
	with open('strain_all.dat', 'r') as f:
		strain_ave = []
		for line in f.readlines():
			strain_ave.append(list(map(float, line.split('\t')[:2])))
	#
	file_names.append('ave_all_gt.dat')
	plot_multi(file_names, 'gt_ave_axis.plt')
	# print(len(stress_ave_all))
	# print(strain_ave[0], strain_ave[1])
	return gt_ave_all, strain_ave


###########################################################################
# IO
#----- データをセーブしてからプロット
def plot_all(target, f_data):
	save_data(target, f_data)
	plot(f_data)
	#
	return

#----- 計算結果をターゲットファイル名で保存
def save_data(target, f_data):
	with open(f_data,'w') as f:
		for line in target:
			for data in line:
				f.write(str(data) + '\t')
			f.write('\n')
	return

#----- 結果をプロット
def plot(f_data):
	plt = make_script(f_data)
	#
	if platform.system() == "Windows":
		subprocess.call([plt], shell=True)
	elif platform.system() == "Linux":
		subprocess.call(['gnuplot ' + plt], shell=True)
	return

# 必要なスクリプトを作成
def make_script(f_data):
	script = script_content(f_data)
	plt = f_data.replace('dat', 'plt')
	with open(plt, 'w') as f:
		f.write(script)
	return plt

# スクリプトの中身
def script_content(f_data):
	out_png = f_data.replace('dat', 'png')
	script = 'set term pngcairo font "Arial,14"\n\n'
	script += 'set colorsequence classic\n\n'
	script += 'data = "' + f_data + '"\n\n'
	script += 'set output "' + out_png + '"\n\n'
	script += 'set key left\nset size square\n'
	script += '#set xrange [1:4]\n#set yrange [0:0.2]\n#set xtics 1\n#set ytics 0.1\n'
	if f_data == 'ss.dat':
		script += 'set y2tics\n'
		script += 'set xlabel "Strain"\nset ylabel "Stress"\nset y2label "Temp."\n'
		script += 'plot data u 1:2 axis x1y1 w l lw 2 lt 1 ti "Stress", \\\n'
		script += 'data u 1:3 axis x1y2 w l lw 2 lt 2 ti "Temp."'
	elif f_data == 'stress_step.dat':
		script += 'set xlabel "Time"\nset ylabel "Stress"\n'	
		script += 'plot	data u 1:2 axis x1y1 w l lw 2 lt 1 ti "Stress"'
	elif f_data == 'strain_step.dat':
		script += 'set y2tics\n'
		script += 'set xlabel "Time"\nset ylabel "Strain"\nset y2label "Temp."\n'	
		script += 'plot	data u 1:2 axis x1y1 w l lw 2 lt 1 ti "Strain", \\\n'
		script += 'data u 1:3 axis x1y2 w l lw 2 lt 2 ti "Temp."'
	elif f_data == 'stress_all.dat' or f_data == 'ave_all_gt.dat':
		script += 'set logscale xy\n'
		script += 'set format x "10^{%L}" \nset format y "10^{%L}"\n'
		script += 'set xlabel "Time"\nset ylabel "Stress"\n'	
		script += 'plot	data u 1:2 axis x1y1 w l lw 2 lt 1 ti "Stress"'
	elif f_data == 'strain_all.dat':
		script += 'set y2tics\n'
		script += 'set logscale xy\n'
		script += 'set format x "10^{%L}" \nset format y "10^{%L}"\n'
		script += 'set xlabel "Time"\nset ylabel "Strain"\nset y2label "Temp."\n'	
		script += 'plot	data u 1:2 axis x1y1 w l lw 2 lt 1 ti "Strain", \\\n'
		script += 'data u 1:3 axis x1y2 w l lw 2 lt 2 ti "Temp."'
	elif f_data == 'ave_all_strain.dat':
		script += 'set logscale xy\n'
		script += 'set format x "10^{%L}" \nset format y "10^{%L}"\n'
		script += 'set xlabel "Time"\nset ylabel "Strain"\n'	
		script += 'plot	data u 1:2 axis x1y1 w l lw 2 lt 1 ti "Strain"'
	elif f_data == 'mod_data.dat' or f_data == 'freq_mod.dat':
		script += 'set logscale xy\n'
		script += 'set format x "10^{%L}" \nset format y "10^{%L}"\n'
		script += 'set xlabel "Time"\nset ylabel "Stress"\n'	
		script += 'plot	data u 1:2 axis x1y1 w l lw 2 lt 1 ti "Stress"'
	elif f_data == 'gt_step.dat' or f_data == 'gt_all.dat':
		script += 'set logscale xy\n'
		script += 'set format x "10^{%L}" \nset format y "10^{%L}"\n'
		script += 'set xlabel "Time"\nset ylabel "G(t)"\n'	
		script += 'plot	data u 1:2 axis x1y1 every ::1 w l lw 2 lt 1 ti "G(t)"'
	script += '\n\nreset'

	return script

#----- 結果をプロット
def plot_multi(file_names, plt):
	make_multiscript(file_names, plt)
	# #
	if platform.system() == "Windows":
		subprocess.call([plt], shell=True)
	elif platform.system() == "Linux":
		subprocess.call(['gnuplot ' + plt], shell=True)
	return


# 必要なスクリプトを作成
def make_multiscript(file_names, plt):
	script = multiscript_content(file_names, plt)
	with open(plt, 'w') as f:
		f.write(script)
	return plt

# スクリプトの中身
def multiscript_content(file_names, plt):
	out_png = plt.replace('plt', 'png')
	script = 'set term pngcairo font "Arial,14"\n\n'
	script += 'set colorsequence classic\n\n'
	for i, file_name in enumerate(file_names):
		script += 'data' + str(i) + '  = "' + file_name + '"\n'
	script += 'set output "' + out_png + '"\n\n'
	script += 'set size square\n'
	script += 'set logscale xy\n#set xrange [1:4]\n#set yrange [0:0.2]\n#set xtics 1\n#set ytics 0.1\n'
	script += 'set format x "10^{%L}" \nset format y "10^{%L}"\n'
	#
	script += 'set xlabel "Time"\nset ylabel "Stress"\n'
	script += 'plot '
	for i, file_name in enumerate(file_names):
		script += 'data' + str(i) + ' u 1:2 w l lw 2 ti "ave-' + str(((file_name.split('.')[0]).split('_')[1])) + '", \\\n'
	script += '\n\nreset'

	return script


##################################
# 
def irheo(data_list):
	minmax = [1e-5, 1e5]
	div = 10
	# print(len(data_list))
	# mod = modify(data_list)
	gt, mod_gt = modify_data(data_list)
	# save_data(mod_gt, 'modified.dat')
	# plotgtgw('modified.dat')
	gw = calcgw(mod_gt, minmax, div)
	save_data(gw, 'gw.dat')
	plotgtgw('gw.dat')
	#
	return

def corrtogw(data_file):
	gw_name = 'gw_' + data_file
	cmd = "corr2gw < " + data_file + " > " + gw_name
	subprocess.call(cmd, shell=True)

	return gw_name

def modify_data(data_list):
	fine_div = 100
	#
	glist = []
	timelist = []
	for data in data_list:
		time = data[0]
		# print(time)
		g = data[1]
		if time == 0.0:
			timelist.append(time)
			glist.append(g)
		else:
			for i in range(1, fine_div + 1):
				timelist.append(pre_time + i*(time-pre_time)/fine_div)
				glist.append(pre_g + i*(g-pre_g)/fine_div)
		pre_time = time
		pre_g = g
		#
	mod_g = signal.savgol_filter(glist, 5, 3)
	#
	gt = np.stack([timelist, glist], 1)
	mod_gt = np.stack([timelist, mod_g], 1)
	#
	return gt, mod_gt

def calcgw(gt, minmax, div):
	gw = []
	mag = math.log10(minmax[0])
	while mag < math.log10(minmax[1]):
		for i in range(div):
			omega = 10**(mag+i/div)
			gstar = gs(gt, omega)
			gw.append([omega, gstar.real, abs(gstar.imag)])
		mag += 1
	#
	return gw

def gs(gt, omega):
	gstar = gt[0][1] + (1 - cmath.exp(-1j*omega*gt[1][0]))*(gt[1][1] - gt[0][1])/gt[1][0]/(1j*omega)
	for k in range(len(gt) - 2):
		gstar += (gt[k+2][1] - gt[k+1][1])*(cmath.exp(-1j*omega*gt[k+1][0]) - cmath.exp(-1j*omega*gt[k+2][0]))/(gt[k+2][0] - gt[k+1][0])/(1j*omega)
	#
	return gstar 

#----- 結果をプロット
def plotgtgw(f_data):
	plt = make_gtgw(f_data)
	#
	if platform.system() == "Windows":
		subprocess.call([plt], shell=True)
	elif platform.system() == "Linux":
		subprocess.call(['gnuplot ' + plt], shell=True)
	return

# 必要なスクリプトを作成
def make_gtgw(f_data):
	script = gtgw_content(f_data)
	plt = f_data.replace('dat', 'plt')
	with open(plt, 'w') as f:
		f.write(script)
	return plt

# スクリプトの中身
def gtgw_content(f_data):
	out_png = f_data.replace('dat', 'png')
	script = 'set term pngcairo font "Arial,14"\n\n'
	script += 'set colorsequence classic\n\n'
	script += 'data = "' + f_data + '"\n\n'
	script += 'set output "' + out_png + '"\n\n'
	script += 'set key left\nset size square\n'
	script += '#set xrange [1:4]\n#set yrange [0:0.2]\n#set xtics 1\n#set ytics 0.1\n'

	if f_data == 'modified.dat' or f_data == 'ave_all_stress.dat':
		script += 'set logscale xy\n'
		script += 'set format x "10^{%L}" \nset format y "10^{%L}"\n'
		script += 'set xlabel "Time"\nset ylabel "Stress"\n'	
		script += 'plot	data u 1:2 axis x1y1 w l lw 2 lt 1 ti "Stress"'
	elif f_data == 'gw.dat' or f_data == 'freq_mod.dat':
		script += 'set xrange [:1e2]\nset yrange [1e-4:]\nset y2range [1e-1:1e1]\nset y2tics\n'
		script += 'set logscale xyy2\n'
		script += '# 斜辺の傾きが -2 の三角形の準備\n'
		script += 'a = 30; # グラフの中に入るように三角形の高さを調整\n'
		script += 'x1=5e-4; x2=1e-3;\n'
		script += 'y1=a*x1**(1);y2=a*x2**(1);\n'
		script += 'set object 1 polygon from x1,y1 to x2,y1 to x2,y2 to x1,y1 fs empty border\n\n'
		script += 'set format x "10^{%L}" \nset format y "10^{%L}"\nset format y2 "10^{%L}"\n'
		# script += 'set label 1 sprintf("{/Symbol l} = %.1f", deform) at graph 0.6, 0.9\n\n'
		script += 'set xlabel "Frequency"\nset ylabel "G' + "', G''" + '"\nset y2label "tan{/Symbol d}"\n\n'
		script += 'plot	'
		script += 'data u 1:2 w lp lt 1 ti "G' + "'" + '", \\\n'
		script += 'data u 1:3 w lp lt 2 ti "G' + "''" + '", \\\n'
		script += 'data u 1:($3/$2) axis x1y2 w lp lt 3 ti "tan{/Symbol d}"'
	script += '\n\nreset'

	return script











def modify(data_list):
	a = 0.057
	tau = 190
	fitstart = 500
	mod_gt = []
	for data in data_list:
		time = float(data[0])
		g = float(data[1])
		if time < fitstart:
			# if g > 0:
			mod_gt.append([time, g])
		else:
			break
	time = fitstart
	while time < 1e5:
		tmp = a*np.exp(-time/tau)
		if tmp > 1e-10:
			mod_gt.append([time, tmp])
			time += 10**int(np.log10(time))/100
		else:
			break
	# save_data(mod_gt, 'mod_gt.dat')
	return mod_gt
