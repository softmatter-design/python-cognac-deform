#!/usr/bin/env python
# -*- coding: utf-8 -*-
##### Import #############################################
from UDFManager import *
import sys
import os
import numpy as np
import glob
import platform
import subprocess
import scipy.signal as signal
###########################################################
###########################################################
class ReadStress:
	def __init__(self, mode, func, nu, deform, structure, ave_xy):
		self.mode = mode
		self.func = func
		self.nu = nu
		self.deform = deform
		self.structure = structure
		self.ave_xy = ave_xy

	def calc_step_gt(self):
		t_udf = self.file_select_one()
		gt_step, gt_step_mod = self.read_step_stress(t_udf)
		return gt_step, gt_step_mod


	##########################################################
	# 
	#----- File Select
	def file_select_one(self):
		out_list = glob.glob('Step_*_out.udf')
		time = 0
		for udf in out_list:
			mtime = os.stat(udf).st_mtime
			if mtime > time:
				time = mtime
				latest_udf = udf
		return latest_udf

	#-----
	def read_step_stress(self, t_udf):
		print("Readin file = ", t_udf)
		area_init, z_init = self.calc_init(t_udf)
		uobj = UDFManager(t_udf)
		time = []
		strain = []
		g = []
		stress = []
		temp = []
		# データ読み込み
		prev_stress = 0.
		prev_g = 0.
		for rec in range(uobj.totalRecord()):
			print("Reading Rec.=", rec)
			uobj.jump(rec)
			#
			time.append(uobj.get("Time"))
			if self.mode == 'elong':
				tmp_strain = uobj.get("Structure.Unit_Cell.Cell_Size.c")/z_init
			elif self.mode == 'shear':
				tmp_strain = uobj.get('Structure.Unit_Cell.Shear_Strain')
			strain.append(tmp_strain)
			#
			if rec == 0:
				tmp_stress = prev_stress
				tmp_g = prev_g
				temp.append(1.)
			else:
				temp.append(uobj.get('Statistics_Data.Temperature.Batch_Average'))
				if self.mode == 'elong':
					stress_list = uobj.get("Statistics_Data.Stress.Total.Batch_Average")
					tmp_stress = stress_list[2]-(stress_list[0] + stress_list[1])/2.
					tmp_g = tmp_stress/(tmp_strain**2 - 1/tmp_strain)
				elif self.mode == 'shear':
					tmp_stress = uobj.get('Statistics_Data.Stress.Total.Batch_Average.xy') - self.ave_xy
					tmp_g = tmp_stress/tmp_strain
				if tmp_stress <= 0:
					tmp_stress = prev_stress
					tmp_g = prev_g
			stress.append(tmp_stress)
			g.append(tmp_g)
			#
			prev_stress = tmp_stress
			prev_g = tmp_g
		#
		mod_g = signal.savgol_filter(g, 11, 3)
		#
		gt_step_mod = np.stack([time, mod_g, temp], 1)
		gt_step = np.stack([time, g, temp], 1)
		ss_step = np.stack([strain, stress, temp], 1)
		
		self.save_data(ss_step, 'ss_step.dat')
		self.save_data(gt_step, 'gt_step.dat')
		self.save_data(gt_step_mod, 'gt_step_mod.dat')
		return gt_step, gt_step_mod

	def calc_init(self, target):
		uobj = UDFManager(target)
		uobj.jump(0)
		#
		cell = uobj.get("Structure.Unit_Cell.Cell_Size")
		area_init = cell[0]*cell[1]
		z_init = cell[2]
		#
		uobj.jump(1)
		vol = uobj.get("Statistics_Data.Volume.Batch_Average")
		return area_init, z_init

	#----- 計算結果をターゲットファイル名で保存
	def save_data(self, target, f_data):
		with open(f_data,'w') as f:
			for line in target:
				for data in line:
					f.write(str(data) + '\t')
				f.write('\n')
		self.plot(f_data)
		return

	#----- 結果をプロット
	def plot(self, f_data):
		plt = self.make_script(f_data)
		#
		if platform.system() == "Windows":
			subprocess.call([plt], shell=True)
		elif platform.system() == "Linux":
			subprocess.call(['gnuplot ' + plt], shell=True)
		return
	
	# 必要なスクリプトを作成
	def make_script(self, f_data):
		script = self.script_content(f_data)
		plt = f_data.replace('dat', 'plt')
		with open(plt, 'w') as f:
			f.write(script)
		return plt

	# スクリプトの中身
	def script_content(self, f_data):
		out_png = f_data.replace('dat', 'png')
		script = 'set term pngcairo font "Arial,14"\n\n'
		script += 'set colorsequence classic\n\n'
		script += 'data = "' + f_data + '"\n\n'
		script += 'set output "' + out_png + '"\n\n'
		script += 'set key left\nset size square\n'
		script += '#set xrange [1:4]\n#set yrange [0:0.2]\n#set xtics 1\n#set ytics 0.1\nset y2tics\n'
		if f_data == 'ss_step.dat':
			script += 'set xlabel "Strain"\nset ylabel "(Nominal) Stress"\nset y2label "Temp."\n'
			script += 'plot data u 1:2 axis x1y1 w l lw 2 lt 1 ti "stress", \\\n'
		else:
			script += 'set xlabel "Time"\nset ylabel "G(t)"\nset y2label "Temp."\n'	
			script += 'plot	data u 1:2 axis x1y1 w l lw 2 lt 1 ti "G(t)", \\\n'
		script += 'data u 1:3 axis x1y2 w l lw 2 lt 2 ti "Temp."'
		script += '\n\nreset'

		return script

	#########################################################################
	# 
	def calc_quench(self, gt_step, gt_step_mod):
		t_udf_list = self.file_select()
		gt_quench_part, gt_quench_part_mod = self.read_gt_quench(t_udf_list)
		gt_all, gt_quench = self.make_series(gt_quench_part, gt_step)
		gt_all_mod, gt_quench_mod = self.make_series(gt_quench_part_mod, gt_step_mod)
		# gt_quench_sm = self.smooth(gt_quench, position = 1, condition = [51, 3])
		# gt_all_sm = self.smooth(gt_all, position = 1, condition = [51, 3])
		self.plot_gt(gt_all, 'gt_all.dat')
		self.plot_gt(gt_quench, 'gt_quench.dat')
		self.plot_gt(gt_all_mod, 'gt_all_mod_11_3.dat')
		self.plot_gt(gt_quench_mod, 'gt_quench_mod_11_3.dat')
		return

	#----- File Select
	def file_select(self):
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
	def read_gt_quench(self, t_udf_list):
		gt_quench_part = []
		gt_quench_part_mod = []
		for target in t_udf_list:
			print("Readin file = ", target)
			data, data_mod = self.read_and_calc(target)
			gt_quench_part.append(data)
			gt_quench_part_mod.append(data_mod)
		return gt_quench_part, gt_quench_part_mod

	#----- Read Data
	def read_and_calc(self, target):
		uobj = UDFManager(target)
		time = []
		g = []
		temp = []
		# データ読み込み
		prev_g = 0.
		for i in range(1, uobj.totalRecord()):
			print("Reading Rec.=", i)
			uobj.jump(i)
			#
			time.append(uobj.get("Time"))
			temp.append(uobj.get('Statistics_Data.Temperature.Batch_Average'))
			#
			if self.mode == 'elong':
				stress = uobj.get("Statistics_Data.Stress.Total.Batch_Average")
				tmp_g = (stress[2]-(stress[0] + stress[1])/2.)/(self.deform**2 - 1/self.deform)
			elif self.mode == 'shear':
				tmp_stress = uobj.get('Statistics_Data.Stress.Total.Batch_Average.xy') - self.ave_xy
				tmp_g = tmp_stress/self.deform
			if tmp_g <=0:
				tmp_g = prev_g
			g.append(tmp_g)
			prev_g = tmp_g
		# smoothing
		mod_g = signal.savgol_filter(g, 11, 3)
		# pack up
		data = np.stack([time, g, temp],1)
		data_mod = np.stack([time, mod_g, temp],1)
		return data, data_mod

	def make_series(self, gt_quench_part, gt_step):
		gt_all = list(gt_step)
		gt_quench = []
		prev_time = 0.
		prev_time_all = gt_all[-1][0]
		for i, g_list in enumerate(gt_quench_part):
			for j in g_list:
				gt_quench.append([j[0] + prev_time, j[1], j[2]])
				gt_all.append([j[0] + prev_time_all, j[1], j[2]])
			prev_time = gt_quench[-1][0]
			prev_time_all = gt_all[-1][0]
		gt_quench.insert(0, [0.0, gt_quench[0][1], gt_quench[0][2]])
		return gt_all, gt_quench

	def smooth(self, data, position, condition):
		data_ar = np.array(data)
		data = data_ar[:, position]
		mod_data = signal.savgol_filter(data, condition[0], condition[1])
		mod_list = np.concatenate([data_ar[:, :position], mod_data.reshape(data.shape[0], 1), data_ar[:, position+1:]], 1)
		return mod_list

	#----- 結果をプロット
	def plot_gt(self, data, f_data):
		self.save_data(data, f_data)
		plt = self.make_script_gt(f_data)
		# self.make_script_gw(func, deform, nu)
		if platform.system() == "Windows":
			subprocess.call([plt], shell=True)
			# subprocess.call([self.plt_gw], shell=True)
		elif platform.system() == "Linux":
			subprocess.call(['gnuplot ' + plt], shell=True)
			# subprocess.call(['gnuplot ' + self.plt_gw], shell=True)
		return

	# 必要なスクリプトを作成
	def make_script_gt(self, f_data):
		script = self.script_gt(f_data)
		plt = f_data.replace('dat', 'plt')
		with open(plt, 'w') as f:
			f.write(script)
		return plt

	# スクリプトの中身
	def script_gt(self, f_data):
		out_png = f_data.replace('dat', 'png')
		script = 'set term pngcairo font "Arial,14"\n\n'
		script += '#set mono\nset colorsequence classic\n\n'
		script += 'data = "' + f_data + '"\n\n'
		script += 'set output "' + out_png + '"\n\n'
		script += '#set key left\nset size square\n'
		script += 'set logscale xy\n\n'
		script += 'set xrange [0:]\n#set yrange [0.01:0.03]\n#set xtics 1\n#set ytics (0.01, 0.015, 0.02, 0.03)\n'
		script += 'set xlabel "Time"\nset ylabel "G(t)"\n\n'
		#
		if self.func != 0:
			script += 'G=' + str(self.nu) + '\n'
			script += 'func = ' + str(self.func) + '\n'
			script += 'f1 = (func - 1.)/(func + 1.)\nf2 = 1. - 2./func\n\n'
			#
			script += 'tau = 500\nst = G\neq = G\n'
			script += 's = 200\ne = 100000\n'
			script += 'g(x) = eq -(eq - st)*exp(-x/tau)\n'
			script += 'fit [s:e] g(x) data via st, eq, tau\n\n'
			#
			script += 'set label 1 sprintf("{/Symbol t} = %.2e", tau) at graph 0.1, 0.2\n'
			# script += 'set label 2 sprintf("{/Symbol s}(0) = %.3e", st) at graph 0.1, 0.2\n'
			script += 'set label 3 sprintf("{/Symbol s}_{eq} = %.2e", eq) at graph 0.1, 0.1\n'
			script += 'set label 4 "{/Symbol s}_{nom}(t) = {/Symbol s}_{eq} - ({/Symbol s}_{eq} - {/Symbol s}(0))*exp(-t/{/Symbol t})" at graph 0.2, 0.6\n'
			script += 'set label 5 sprintf("fitting region: from %.d", s) at graph 0.1, 0.3\n'
			script += 'set label 6 sprintf("{/Symbol n}k_BT = %.2e", G) at graph 0.6, 0.1\n\n'
		#
		script += 'plot	'
		script += 'data u 1:2 w l lw 2 lt 1 ti "Quench from {/Symbol l}= ' + str(round(self.deform, 2)) + '"'
		if self.func != 0:
			script += ', \\\n [s:e] g(x) w l lw 2 lt 2 ti "fit", \\\n'
			script += '[1000:] G w l lw 3 dt (10, 5) lt 8 ti "Affin"'
			script += ', \\\n[1000:] G*f1 w l lw 3 dt (10, 5) lt 9 ti "Q. Pht.", \\\n'
			script += '[1000:] G*f2 w l lw 3 dt (10, 5) lt 7 ti "Phantom"'
		script += '\n\nreset'
		return script

	def average(self):
		target = ['gt_all']
		for name in target:
			dat_list = glob.glob('**/' + name + '.dat', recursive = True)
			val_list = []
			for dat in dat_list:
				with open(dat, 'r') as f:
					tmp = []
					time = []
					for line in f.readlines():
						tmp.append(float(line.split('\t')[1]))
						time.append(float(line.split('\t')[0]))
					val_list.append(tmp)
			ave_list = np.average(np.array(val_list), axis = 0)
			res = np.stack([time, ave_list], 1)





	# def make_script_gw(self, func, deform, nu):
	# 	script_gw = self.script_content_gw(func, deform, nu)
	# 	with open(self.plt_gw, 'w') as f:
	# 		f.write(script_gw)
	# 	return

	# 	m
	# # スクリプトの中身
	# def script_content_gw(self, func, deform, nu):
	# 	script = 'set term pngcairo font "Arial,14"\n\n'
	# 	script += '#set mono\nset colorsequence classic\n\n'
	# 	script += 'data = "' + self.f_data_gw + '"\n\n'
	# 	script += 'set output "' + self.out_png_gw + '"\n\n'
	# 	script += 'set key left\nset size square\n\n'
	# 	script += 'set y2tics\nset logscale xyy2\n'
	# 	script += 'set format x "10^{%L}"\nset format y "10^{%L}"\nset format y2 "10^{%L}"\n\n'
	# 	script += 'set xrange [1e-4:10]\nset yrange [0.01:10]\nset y2range[0.1:10]\n\n'
	# 	script += 'set xlabel "Frequency"\nset ylabel "G' + "', G''" + '"\nset y2label "tan{/Symbol d}"\n\n'
	# 	#
	# 	if func != 0:
	# 		script += 'G=' + str(nu) + '\n'
	# 		script += 'func = ' + str(func) + '\n'
	# 		script += 'deform = ' + str(deform) + '\n'
	# 	#
	# 	script += '# 斜辺の傾きが -2 の三角形の準備\n'
	# 	script += 'a = 30; # グラフの中に入るように三角形の高さを調整\n'
	# 	script += 'x1=5e-4; x2=1e-3;\n'
	# 	script += 'y1=a*x1**(1);y2=a*x2**(1);\n'
	# 	script += 'set object 1 polygon from x1,y1 to x2,y1 to x2,y2 to x1,y1 fs empty border\n\n'
	# 	#
	# 	script += 'set label 1 sprintf("{/Symbol l} = %.1f", deform) at graph 0.6, 0.9\n\n'
	# 	if func != 0:
	# 		script += 'set label 2 sprintf("{/Symbol n}k_BT = %.2e", G) at graph 0.6, 0.8\n\n'
	# 	#
	# 	script += 'plot	'
	# 	script += 'data u 1:2 w lp lt 1 ti "G' + "'" + '", \\\n'
	# 	script += 'data u 1:3 w lp lt 2 ti "G' + "''" + '", \\\n'
	# 	script += 'data u 1:($3/$2) axis x1y2 w lp lt 3 ti "tan{/Symbol d}"'
	# 	if func != 0:
	# 		script += ', \\\n[1e-4:1e-3] G w l lw 4 lt 8 dt (10, 5) ti "{/Symbol n}k_BT"'
	# 	script += '\n\nreset'

	# 	return script
















