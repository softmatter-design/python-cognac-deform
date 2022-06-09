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
from operator import itemgetter

import evaluate_simple_deform.values as val
###########################################################
# print("This is module!")
###########################################################
def simple_deform():
	file_listing()
	calc_stress_all()
	save_data()
	plot()
	return
#----- File Select
def file_listing():
	target = '*_out.udf'
	udf_list = glob.glob(target)
	val.def_mode = udf_list[0].split('_')[0]
	tmp = sorted([[i, float(i.split('_')[2])] for i in udf_list], key= itemgetter(1), reverse=True)
	val.sorted_udf = list(np.array(tmp)[:,0])
	return 
#-----
def calc_stress_all():
	val.ss_data = []
	for target in val.sorted_udf:
		print("Readin file = ", target)
		#
		val.ss_data.append(read_and_calc(target))
	return

#----- Read Data
def read_and_calc(target):
	uobj = UDFManager(target)
	data = []
	#
	uobj.jump(0)
	cell = uobj.get("Structure.Unit_Cell.Cell_Size")
	area_init = cell[0]*cell[1]
	z_init = cell[2]
	for i in range(1, uobj.totalRecord()):
		print("Reading Rec.=", i)
		uobj.jump(i)
		if val.def_mode == 'Shear':
			stress = uobj.get('Statistics_Data.Stress.Total.Batch_Average.xy')
			strain = uobj.get('Structure.Unit_Cell.Shear_Strain')
		elif val.def_mode == 'Elong':
			cell = uobj.get("Structure.Unit_Cell.Cell_Size")
			stress_list = uobj.get("Statistics_Data.Stress.Total.Batch_Average")
			stress = (cell[0]*cell[1])*(stress_list[2]-(stress_list[0] + stress_list[1])/2.)/area_init
			strain = uobj.get("Structure.Unit_Cell.Cell_Size.c")/z_init
		data.append([strain, stress])
	return data

#----- 計算結果をターゲットファイル名で保存
def save_data():
	for i, target_udf in enumerate(val.sorted_udf):
		target_rate = str(target_udf.split("_")[2])
		target = "SS_rate_" + target_rate + '.dat'
		val.ss_data_list.append(target)
		with open(target,'w') as f:
			f.write('# Strain\tStress\n\n')
			for line in val.ss_data[i]:
				f.write(str(line[0]) + '\t' + str(line[1]) + '\n')
	return

#----- 結果をプロット
def plot():
	plot_ss()
	if val.def_mode == 'Elong':
		plot_mr()
	return

# 必要なスクリプトを作成
def plot_ss():
	script_content()
	with open(val.plt_file, 'w') as f:
		f.write(val.script)
	#
	if platform.system() == "Windows":
		subprocess.call([val.plt_file], shell=True)
	elif platform.system() == "Linux":
		subprocess.call(['gnuplot ' + val.plt_file], shell=True)
	return

# スクリプトの中身
def script_content():
	val.script = 'set term pngcairo font "Arial,14"\n\n'
	val.script += '#set mono\nset colorsequence classic\n\n'
	for i, filename in enumerate(val.ss_data_list):
		val.script += 'data' + str(i) + ' = "' + filename + '"\n'
	val.script += 'set output "SS_multi.png"\n\n'
	val.script += 'set key left\nset size square\n'
	val.script += '#set xrange [1:3]\nset yrange [0.:]\n#set xtics 0.5\n#set ytics 0.01\n'
	val.script += 'set xlabel "Strain"\nset ylabel "Stress"\n\n'
	val.script += 'G=' + str(val.nu) + '\nfunc=' + str(val.func) + '\n'
	if val.def_mode = 'Elong':
		val.script += 'f(x,f)=f*G*(x-1./x**2.)\n'
	elif val.def_mode = 'Shear':
		val.script += 'f(x,f)=f*G*((x+1)-1./(x+1)**2.)\n'
	val.script += 'f1=(func-1.)/(func+1.)\nf2=1.-2./func\n\n'
	val.script += 'plot	'
	for i, target in enumerate(val.ss_data_list):
		val.script += 'data' + str(i) + ' w l lw 2 lt ' + str(i+1) + ' ti "rate: ' + (target.split('.')[0]).split('_')[2] + '", \\\n'
	val.script += 'f(x,1) w l lw 2 lt 10 ti "Affin", \\\nf(x,f1) w l lw 2 lt 11 ti "Q. Pht.", \\\nf(x,f2) w l lw 2 lt 12 ti "Phantom"'
	val.script += '\n\nreset'
	return

# 
def plot_mr():
	for target in val.ss_data_list:
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
	script += '#set xrange [0:1]\n#set yrange [0.:0.1]\n#set xtics 0.5\n#set ytics 0.02\n'
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














