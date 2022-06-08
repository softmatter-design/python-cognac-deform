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
	# save_data()
	return
#----- File Select
def file_listing():
	target = '*_out.udf'
	val.sorted_udf = sorted(glob.glob(target))
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
	for i in range(1, uobj.totalRecord()):
		print("Reading Rec.=", i)
		uobj.jump(i)
		#
		stress = uobj.get('Statistics_Data.Stress.Total.Batch_Average.xy')
		strain = uobj.get('Structure.Unit_Cell.Shear_Strain')
		data.append([strain, stress])
	return data

#----- 計算結果をターゲットファイル名で保存
def save_data():
	tmp_list = []
	for i, target_udf in enumerate(val.sorted_udf):
		target_rate = str(target_udf.split("_")[2])
		target = "SS_rate_" + target_rate + '.dat'
		tmp_list.append([[target, target_rate], target_rate.split("e")[0], target_rate.split("e")[1]])
		with open(target,'w') as f:
			f.write('# Strain\tStress\n\n')
			for line in val.ss_data[i]:
				for data in line:
					f.write(str(data) + '\t')
				f.write('\n')

	#
	tmp2 = list(np.array(sorted(tmp_list, key = itemgetter(1), reverse = True)))
	sorted_target = list(np.array(sorted(tmp2, key = itemgetter(2)))[:,0])

	return sorted_target


#----- 結果をプロット
def plot(target_list):
	plt_file = 'plot_SS_multi.plt'
	make_script(plt_file, target_list)
	#
	if platform.system() == "Windows":
		subprocess.call([plt_file], shell=True)
	elif platform.system() == "Linux":
		subprocess.call(['gnuplot ' + plt_file], shell=True)
	return

# 必要なスクリプトを作成
def make_script(plt_file, target_list):
	script = script_content(target_list)
	with open(plt_file, 'w') as f:
		f.write(script)
	return

# スクリプトの中身
def script_content(target_list):
	script = 'set term pngcairo font "Arial,14"\n\n'
	script += 'set output "SS_multi.png"\n\n'
	script += 'set key left\nset size square\n'
	script += '#set xrange [1:3]\n#set yrange [0.:0.1]\n#set xtics 0.5\n#set ytics 0.01\n'
	script += 'set xlabel "Strain"\nset ylabel "Stress"\n\n'
	script += 'plot	'
	for i, target in enumerate(target_list, 1):
		script += '"' + str(target[0]) + '" w l lw 2 lt ' + str(i) + ' ti "rate: ' + str(target[1]) + '", \\\n'
	script += '0.0176*x w l lw 2 lt 8 \n'
	script += '\n\nreset'

	return script

def plot_mr(target_list):
	for target in target_list:
		mr(target)


def mr(target):
	plt_file = 'plot_MR_rate_' + target[1] + '.plt'
	make_script2(plt_file, target)
	#
	if platform.system() == "Windows":
		subprocess.call([plt_file], shell=True)
	elif platform.system() == "Linux":
		subprocess.call(['gnuplot ' + plt_file], shell=True)
	return

# 必要なスクリプトを作成
def make_script2(plt_file, target):
	script = script_content2(target)
	with open(plt_file, 'w') as f:
		f.write(script)
	return

# スクリプトの中身
def script_content2(target):
	script = 'set term pngcairo font "Arial,14"\n\n'
	script += '#set mono\nset colorsequence classic\n\n'
	script += 'data = "' + target[0] + '" \n'
	script += 'set output "MR_rate_' + target[1] + '.png"\n\n'
	script += 'set key left\nset size square\n'
	script += 'set xrange [0:1]\nset yrange [0.:0.1]\nset xtics 0.5\nset ytics 0.02\n'
	script += 'set xlabel "1/{/Symbol l}"\nset ylabel "{/Symbol s}/({/Symbol l}-1/{/Symbol l}^2)"\n\n'
	script += '## Fit Range\n\nlow = 0.3\nhigh = 0.5\n\n'
	script += 'fit [low:high] a*x+b data usi ( 1/$1 ):( $2/( $1 - 1/( $1**2 ) ) ) via a,b\n\n'
	script += 'set label 1 sprintf("C1 = %.3f", b/2) left at graph 0.2,0.8\n'
	script += 'set label 2 sprintf("C2 = %.3f", a/2) left at graph 0.2,0.7\n'
	script += 'set label 3 sprintf("fit range = %.3f to %.3f", low, high) left at graph 0.2,0.6\n\n#\n'
	script += 'plot data usi ( 1/$1 ):( $2/( $1 - 1/( $1**2 ) ) ) w lp pt 7 lt 1 ti "Original Data", \\\n'
	script += '[low:high] a*x + b w l lw 5 lt 2 ti "Fitted Line"'
	script += '\n\nreset'

	return script















