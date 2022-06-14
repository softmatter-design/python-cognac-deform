#!/usr/bin/env python
# -*- coding: utf-8 -*-
##### Import #############################################
from UDFManager import *
import argparse
import numpy as np
import glob
import platform
import subprocess
import sys
from operator import itemgetter

import evaluate_simple_deform.values as val
###########################################################
# print("This is module!")
###########################################################
def cyclic_deform():
	setup()
	calc_stress_all()
	save_data()
	plot_ss()
	return

##############
def setup():
	read_arg()
	file_listing()
	return
# Read argument 
def read_arg():
	parser = argparse.ArgumentParser(description='Evaluate deformed simulations !')
	parser.add_argument('-f','--func', type=int, help="Functionality of junction point (int).")
	parser.add_argument('-n', '--nu', type=float, help="Strand density of network (float).")
	parser.add_argument('-m', '--mode', help="Mode of deformation; Shear or Stretch")
	parser.add_argument('-d', '--deform', help="Maximum value of deformation")
	args = parser.parse_args()
	if args.func and args.nu:
		val.func = args.func
		val.nu = args.nu
		val.cyc_deform_max = args.deform
	else:
		print('\n#####\nfunctionality and/or nu is not specified')
		print('Default value will be used!')
	if args.mode:
		val.cyc_def_mode = args.mode
	else:
		print('\n#####\ndeformation mode is not set!')
		sys.exit('either mode of shear or stretch should be set!')
	if args.deform:
		val.cyc_deform_max = args.deform
	else:
		print('\n#####\nMax deformation is not set !')
		sys.exit('this value should be set!')
	return
# File Select
def file_listing():
	target = '*_out.udf'
	udf_list = glob.glob(target)
	if udf_list:
		tmp = sorted(udf_list, reverse=True)
		for i in range(int(len(tmp)/2)):
			val.sorted_udf.append(tmp[-2*(i+1):len(tmp)-2*i])
	else:
		sys.exit('\n#####\nNo effective *_out.udf file in this directory !!\nSomething wrong !!\n')
	return 

############################
# Calculate stress either for Shear or Stretch deformation
def calc_stress_all():
	val.ss_data = []
	for list in val.sorted_udf:
		tmp_data = []
		for target in list:
			print("Readin file = ", target)
			tmp_data.extend(read_and_calc(target))
		val.ss_data.append(tmp_data)
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
		if val.cyc_def_mode == 'shear':
			stress = uobj.get('Statistics_Data.Stress.Total.Batch_Average.xy')
			if target.split('_')[1] == 'Forward':
				strain = uobj.get('Structure.Unit_Cell.Shear_Strain')
			else:
				strain = float(val.cyc_deform_max) + float(uobj.get('Structure.Unit_Cell.Shear_Strain'))
		elif val.cyc_def_mode == 'stretch':
			cell = uobj.get("Structure.Unit_Cell.Cell_Size")
			stress_list = uobj.get("Statistics_Data.Stress.Total.Batch_Average")
			stress = (cell[0]*cell[1])*(stress_list[2]-(stress_list[0] + stress_list[1])/2.)/area_init
			strain = uobj.get("Structure.Unit_Cell.Cell_Size.c")/z_init
		data.append([str(strain), stress])
	return data

########################################
# 計算結果をターゲットファイル名で保存
def save_data():
	with open('SS.dat', 'w') as f:
		f.write('# Strain\tStress\n\n')
		for data in val.ss_data:
			for line in data:
				f.write(str(line[0]) + '\t' + str(line[1]) + '\n')
			f.write('\n\n')
	return

############################
# 結果をプロット
def plot_ss():
	script_content()
	with open('plot_ss.plt', 'w') as f:
		f.write(val.script)
	#
	if platform.system() == "Windows":
		subprocess.call(['plot_ss.plt'], shell=True)
	elif platform.system() == "Linux":
		subprocess.call(['gnuplot ' + 'plot_ss.plt'], shell=True)
	return

# スクリプトの中身
def script_content():
	val.script = 'set term pngcairo font "Arial,14"\n\n'
	val.script += '#set mono\nset colorsequence classic\n\n'
	val.script += 'data = "SS.dat"\n'
	val.script += 'set output "SS_multi.png"\n\n'
	val.script += 'set key left\nset size square\n'
	val.script += '#set xrange [1:3]\nset yrange [0.:]\n#set xtics 0.5\n#set ytics 0.01\n'
	val.script += 'set xlabel "Strain"\nset ylabel "Stress"\n\n'
	val.script += 'G=' + str(val.nu) + '\nfunc=' + str(val.func) + '\n'
	if val.cyc_def_mode == 'stretch':
		val.script += 'f(x,f)=f*G*(x-1./x**2.)\n'
		val.script += '#f(x,f)=f*G*((x+1)-1./(x+1)**2.)\n'
		val.script += '#for shear uncomment and use 2nd eq\n'
	elif val.cyc_def_mode == 'shear':
		val.script += 'f(x,f)=f*G*((x+1)-1./(x+1)**2.)\n'
	val.script += 'f1=(func-1.)/(func+1.)\nf2=1.-2./func\n\n'
	val.script += 'plot '
	for i in range(len(val.ss_data)):
		val.script += 'data ind ' + str(i) + ' w l lw 2 lt ' + str(i+1) + ' ti "#' + str(i) + '", \\\n'
	val.script += 'f(x,1) w l lw 2 lt 10 ti "Affin", \\\nf(x,f1) w l lw 2 lt 11 ti "Q. Pht.", \\\nf(x,f2) w l lw 2 lt 12 ti "Phantom"'
	val.script += '\n\nreset'
	return












