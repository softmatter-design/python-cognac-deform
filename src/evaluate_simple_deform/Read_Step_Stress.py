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
	def __init__(self, mode): #, func, nu, deform, structure, ave_xy):
		self.mode = mode

	def calc_step(self):
		t_udf = self.file_select_one()
		stress_step, strain_step = self.read_step_stress(t_udf)
		return stress_step, strain_step


	##########################################################
	# 
	#----- File Select: Select latest udf data
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
		stress = []
		temp = []
		# データ読み込み
		prev_stress = 0.
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
				temp.append(1.)
			else:
				temp.append(uobj.get('Statistics_Data.Temperature.Batch_Average'))
				if self.mode == 'elong':
					stress_list = uobj.get("Statistics_Data.Stress.Total.Batch_Average")
					tmp_stress = stress_list[2]-(stress_list[0] + stress_list[1])/2.
				elif self.mode == 'shear':
					tmp_stress = uobj.get('Statistics_Data.Stress.Total.Batch_Average.xy') #- self.ave_xy
				if tmp_stress <= 0:
					tmp_stress = prev_stress
			stress.append(tmp_stress)
			#
			prev_stress = tmp_stress
		#
		stress_step = np.stack([time, stress, temp], 1)
		strain_step = np.stack([time, strain, temp], 1)
		ss = np.stack([strain, stress, temp], 1)
		
		self.plot(strain_step, 'strain_step.dat')
		
		self.plot(stress_step, 'stress_step.dat')
		self.plot(ss, 'ss.dat')
		return stress_step, strain_step

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
		return

	#----- 結果をプロット
	def plot(self, target, f_data):
		self.save_data(target, f_data)
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
		elif f_data == 'stress_all.dat' or f_data == 'ave_all_stress.dat':
			script += 'set logscale xy\n'
			script += 'set xlabel "Time"\nset ylabel "Stress"\n'	
			script += 'plot	data u 1:2 axis x1y1 w l lw 2 lt 1 ti "Stress"'
		elif f_data == 'strain_all.dat':
			script += 'set y2tics\n'
			script += 'set logscale xy\n'
			script += 'set xlabel "Time"\nset ylabel "Strain"\nset y2label "Temp."\n'	
			script += 'plot	data u 1:2 axis x1y1 w l lw 2 lt 1 ti "Strain", \\\n'
			script += 'data u 1:3 axis x1y2 w l lw 2 lt 2 ti "Temp."'
		elif f_data == 'ave_all_strain.dat':
			script += 'set logscale xy\n'
			script += 'set xlabel "Time"\nset ylabel "Strain"\n'	
			script += 'plot	data u 1:2 axis x1y1 w l lw 2 lt 1 ti "Strain"'
		script += '\n\nreset'

		return script

	#----- 結果をプロット
	def plot_multi(self, target, f_data):
		self.save_data(target, f_data)
		plt = self.make_script(f_data)
		#
		if platform.system() == "Windows":
			subprocess.call([plt], shell=True)
		elif platform.system() == "Linux":
			subprocess.call(['gnuplot ' + plt], shell=True)
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
	def read_quench(self, t_udf_list, c_strain):
		stress_quench = []
		strain_quench = []
		for target in t_udf_list:
			print("Readin file = ", target)
			stress_part, strain_part = self.read_and_calc(target, c_strain)
			stress_quench.append(stress_part)
			strain_quench.append(strain_part)
		return stress_quench, strain_quench

	#----- Read Data
	def read_and_calc(self, target, c_strain):
		uobj = UDFManager(target)
		time = []
		temp = []
		stress = []
		strain = []
		# データ読み込み
		prev_stress = 0.
		for i in range(1, uobj.totalRecord()):
			print("Reading Rec.=", i)
			uobj.jump(i)
			#
			time.append(uobj.get("Time"))
			temp.append(uobj.get('Statistics_Data.Temperature.Batch_Average'))
			#
			if self.mode == 'elong':
				strs = uobj.get("Statistics_Data.Stress.Total.Batch_Average")
				tmp_stress = strs[2]-(strs[0] + strs[1])/2.
			elif self.mode == 'shear':
				tmp_stress = uobj.get('Statistics_Data.Stress.Total.Batch_Average.xy') #- self.ave_xy
			if tmp_stress <=0:
				tmp_stress = prev_stress
			#
			stress.append(tmp_stress)
			strain.append(c_strain)
			prev_stress = tmp_stress
		#
		stress_part = np.stack([time, stress, temp], 1)
		strain_part = np.stack([time, strain, temp], 1)
		return stress_part, strain_part


	def average(self):
		target = ['stress', 'strain']
		for name in target:
			dat_list = glob.glob('**/' + name + '_all.dat', recursive = True)
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
			data_list = []
			multi_list = []
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
						data_list.append(tmp)
				ax_ave = np.average(np.array(ax_dat_list), axis = 0)
				res_axis = np.stack([time, ax_ave], 1)
				multi_list.append([dat[0], res_axis])
				# self.plot(res_axis, 'ave_'+ dat[0] + '_' + name + ".dat")
			#
			ave_all = np.average(np.array(data_list), axis = 0)
			res_all = np.stack([time, ave_all], 1)
			self.plot(res_all, 'ave_all_'+ name + ".dat")

			# 	with open(dat, 'r') as f:
			# 		tmp = []
			# 		time = []
			# 		for line in f.readlines():
			# 			tmp.append(float(line.split('\t')[1]))
			# 			time.append(float(line.split('\t')[0]))
			# 		val_list.append(tmp)
			# ave_list = np.average(np.array(val_list), axis = 0)
			# res = np.stack([time, ave_list], 1)
			# self.plot(res, 'ave_'+ name + ".dat")




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















	#########################################################################
	# 
	def calc_quench2(self, stress_step, strain_step):
		c_strain = strain_step[-1][1]
		t_udf_list = self.file_select()
		stress_quench, strain_quench = self.read_quench(t_udf_list, c_strain)
		#
		stress_all = self.make_series2(stress_step, stress_quench)
		strain_all = self.make_series2(strain_step, strain_quench)

		self.plot(stress_all, 'stress_all.dat')
		self.plot(strain_all, 'strain_all.dat')

		return


	def make_series2(self, data_step, data_t):
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
		return data_all
