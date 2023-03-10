#!/usr/bin/env python
# -*- coding: utf-8 -*-
##### Import #############################################
# from unittest import result
from UDFManager import *
import argparse
import numpy as np
import glob
import platform
import subprocess
import sys

from scipy.signal import savgol_filter

import evaluate_deform.variables as var
###########################################################
def step_deform():
	read_arg()	
	if not var.ave_flag:
		calc_stress_all()
	else:
		target = ['gt_all']
		average(target)
	return

# Read argument 
def read_arg():
	parser = argparse.ArgumentParser(description='Evaluate deformed simulations !')
	parser.add_argument('-f','--func', type=int, help="Functionality of junction point (int).")
	parser.add_argument('-n', '--nu', type=float, help="Strand density of network (float).")
	parser.add_argument('-m', '--mode', help="Mode of deformation; shear or stretch")
	# parser.add_argument('-u', '--udf', help="Setting UDF file to read")
	# parser.add_argument('-s', '--step', help="Flag for treating step calculation", action='store_true')
	parser.add_argument('-a', '--average', help="Flag for averaging subdir data", action='store_true')
	args = parser.parse_args()
	if args.func and args.nu:
		var.func = args.func
		var.nu = args.nu
	else:
		print('\n#####\nfunctionality and/or nu is not specified')
		print('Default value will be used!')
	if args.mode:
		var.step_def_mode = args.mode.lower()
	else:
		print('\n#####\ndeformation mode is not set!')
		sys.exit('either mode of shear or stretch should be set!')
	# var.step_flag = args.step
	var.ave_flag = args.average
	return


############################
# Calculate stress either for shear or stretch deformation
def calc_stress_all():
	calc_step_deform('deform_out.udf')
	calc_relax_all()
	return

def calc_step_deform(t_udf):
	print("Readin file = ", t_udf)
	z_init = calc_init(t_udf)
	uobj = UDFManager(t_udf)
	time = []
	strain = []
	g = []
	stress = []
	temp = []
	# データ読み込み
	# prev_stress = 0.
	# prev_g = 0.
	for rec in range(1, uobj.totalRecord()):
		print("Reading Rec.=", rec)
		uobj.jump(rec)
		time.append(uobj.get("Time"))
		temp.append(uobj.get('Statistics_Data.Temperature.Batch_Average'))
		if var.step_def_mode == 'stretch':
			tmp_strain = uobj.get("Structure.Unit_Cell.Cell_Size.c")/z_init
			stress_list = uobj.get("Statistics_Data.Stress.Total.Batch_Average")
			tmp_stress = stress_list[2]-(stress_list[0] + stress_list[1])/2.
			tmp_g = tmp_stress/(tmp_strain**2 - 1/tmp_strain)
		elif var.step_def_mode == 'shear':
			tmp_strain = uobj.get('Structure.Unit_Cell.Shear_Strain')
			tmp_stress = uobj.get('Statistics_Data.Stress.Total.Batch_Average.xy')
			tmp_g = tmp_stress/tmp_strain
		# if tmp_stress <= 0:
		# 	tmp_stress = prev_stress
		# 	tmp_g = prev_g
		strain.append(tmp_strain)
		stress.append(tmp_stress)
		g.append(tmp_g)
		#
		# prev_stress = tmp_stress
		# prev_g = tmp_g
	#
	var.step_strain = tmp_strain
	var.elapsed_time = time[-1]
	#
	var.global_time.extend(time)
	var.global_g.extend(g)
	var.global_temp.extend(temp)
	#
	mod_g = savgol_filter(g, var.savgol_parameter[0], var.savgol_parameter[1])
	#
	gt_step = np.stack([time, g, temp], 1)
	gt_step_mod = np.stack([time, mod_g, temp], 1)
	ss_step = np.stack([strain, stress, temp], 1)
	
	save_data(ss_step, 'ss_step.dat')
	save_data(gt_step, 'gt_step.dat')
	save_data(gt_step_mod, 'gt_step_mod.dat')
	return

def calc_init(target):
	uobj = UDFManager(target)
	uobj.jump(0)
	cell = uobj.get("Structure.Unit_Cell.Cell_Size")
	z_init = cell[2]
	return z_init

#########################################################################
#-----
def calc_relax_all():
	for target in glob.glob('relax*_out.udf') :
		print("Readin file = ", target)
		read_relax(target)
	
	mod_g = savgol_filter(var.global_g, var.savgol_parameter[0], var.savgol_parameter[1])
	total_g = np.stack([var.global_time, var.global_g, var.global_temp],1)
	total_g_mod = np.stack([var.global_time, mod_g, var.global_temp],1)
	save_data(total_g, 'gt_all.dat')
	save_data(total_g_mod, 'gt_all_mod.dat')
	return

#----- Read Data
def read_relax(target):
	uobj = UDFManager(target)
	time = []
	g = []
	temp = []
	# prev_g = 0.
	for i in range(1, uobj.totalRecord()):
		print("Reading Rec.=", i)
		uobj.jump(i)
		#
		time.append(uobj.get("Time") + var.elapsed_time)
		temp.append(uobj.get('Statistics_Data.Temperature.Batch_Average'))
		#
		if var.step_def_mode == 'stretch':
			stress_list = uobj.get("Statistics_Data.Stress.Total.Batch_Average")
			tmp_stress = stress_list[2]-(stress_list[0] + stress_list[1])/2.
			tmp_g = tmp_stress/(var.step_strain**2 - 1/var.step_strain)
		elif var.step_def_mode == 'shear':
			tmp_stress = uobj.get('Statistics_Data.Stress.Total.Batch_Average.xy')
			tmp_g = tmp_stress/var.step_strain
		# if tmp_g <=0:
		# 	tmp_g = prev_g
		g.append(tmp_g)
		prev_g = tmp_g
	var.global_time.extend(time)
	var.global_g.extend(g)
	var.global_temp.extend(temp)
	var.elapsed_time = time[-1]
	return

###############################
#----- 計算結果をターゲットファイル名で保存
def save_data(target, f_data):
	with open(f_data,'w') as f:
		for line in target:
			for data in line:
				f.write(str(data) + '\t')
			f.write('\n')
	plot(f_data)
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
	if f_data == 'ss_step.dat':
		script += 'set y2tics\nset xlabel "Strain"\nset ylabel "Stress"\nset y2label "Temp."\n\n'
		script += 'plot data u 1:2 axis x1y1 w l lw 2 lt 1 ti "stress", \\\n'
		script += 'data u 1:3 axis x1y2 w l lw 2 lt 2 ti "Temp."'
	elif f_data == 'gt_step.dat' or f_data =='gt_step_mod.dat':
		script += 'set xlabel "Time"\nset ylabel "G(t)"\n'	
		script += 'set logscale xy\n\n'	
		script += 'plot	data u 1:2 axis x1y1 w l lw 2 lt 1 ti "G(t)"'
	else:
		script += f'G={var.nu:}\nfunc ={var.func:}\n'
		script += 'f1 = (func - 1.)/(func + 1.)\nf2 = 1. - 2./func\n\n'
		script += 'tau = 500\nst = G\neq = G\ns = 500\ne = 100000\n\n'
		script += 'g(x) = eq -(eq - st)*exp(-x/tau)\n'
		script += 'fit [s:e] g(x) data via st, eq, tau\n\n'
		script += 'set label 1 sprintf("fitting region: from %.d", s) at graph 0.2, 0.6\n'
		script += 'set label 2 sprintf("{/Symbol s}_{eq} = %.1e", eq) at graph 0.2, 0.5\n'
		script += 'set label 3 sprintf("{/Symbol t} = %.1e", tau) at graph 0.2, 0.4\n'
		script += '#set label 4 "{/Symbol s}_{nom}(t) = {/Symbol s}_{eq} - ({/Symbol s}_{eq} - {/Symbol s}(0))*exp(-t/{/Symbol t})" at graph 0.2, 0.6\n'
		script += 'set label 5 sprintf("{/Symbol n}k_BT = %.2e", G) at graph 0.2, 0.2\n\n'
		script += 'set xlabel "Time"\nset ylabel "G(t)"\n'	
		script += 'set logscale xy\n\n'	
		script += 'plot	data u 1:2 axis x1y1 w l lw 2 lt 1 ti "G(t)", \\\n'
		script += '[s:e] g(x) w l lw 2 lt 2 ti "fit", \\\n'
		script += '[1000:] G w l lw 3 dt (10, 5) lt 8 ti "Affin", \\\n'
		script += '[1000:] G*f1 w l lw 3 dt (10, 5) lt 9 ti "Q. Pht.", \\\n'
		script += '[1000:] G*f2 w l lw 3 dt (10, 5) lt 7 ti "Phantom"'
	script += '\n\nreset\n\n'
	if f_data == 'gt_all_averaged.dat':
		script += 'set term pngcairo font "Arial,14"\n\n'
		script += 'set colorsequence classic\n\n'
		script += 'data = "' + f_data + '"\n\n'
		script += 'set output "gt_all_averaged_semilog.png"\n\n'
		script += '#set key left\nset size square\n'
		script += f'G={var.nu:}\nfunc ={var.func:}\n'
		script += 'tau = 1000\nst = G\neq = G\ns = 500\ne = 100000\n\n'
		script += 'g(x) = eq -(eq - st)*exp(-x/tau)\n'
		script += 'fit [s:e] g(x) data via st, eq, tau\n\n'
		script += 'a=1\ns2 = 500\ne2 = 1000\n\n'
		script += 'h(x) = a*exp(-x/tau)\n'
		script += 'fit [s2:e2] h(x) data u 1:($2 - eq) via a, tau\n\n'
		script += 'set label 1 "G_{mod}(t) = G(t)-G_0" at graph 0.2, 0.7\n'
		script += 'set label 2 sprintf("fitting region: from %.d", s2) at graph 0.2, 0.6\n'
		script += 'set label 3 sprintf("G_0 = %.1e", eq) at graph 0.2, 0.5\n'
		script += 'set label 4 sprintf("{/Symbol t} = %.1e", tau) at graph 0.2, 0.4\n'
		script += 'set xlabel "Time"\nset ylabel "G_{mod}(t)"\n'	
		script += 'set logscale y\n\n'	
		script += 'set xrange [:e2]\nset yrange [1e-3:]\n#set xtics 1\n#set ytics 0.1\n'
		script += 'plot	data u 1:($2 - eq) axis x1y1 w l lw 2 lt 1 ti "G_{mod}(t)", \\\n'
		script += '[s2:e2] h(x) w l lw 2 lt 2 ti "fit"'
	script += '\n\nreset'
	return script


###############################
def average(target):
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
		save_data(res, name + '_averaged.dat')



