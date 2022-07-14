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
###########################################################
# print("This is module!")
###########################################################
#
def calc_all(func, nu, structure):
	fname = '*_out.udf'
	t_udf_list = file_listing(fname)
	calc_save_stress(t_udf_list, func, nu, structure)
	fname = 'SS*.dat'
	SS_list = file_listing(fname)
	plot(func, nu, structure, SS_list)
	# rs.plot_mr(target_list)
#----- File Select
def file_listing(fname):
	sorted_list = sorted(glob.glob(fname))
	return sorted_list

#-----
def calc_save_stress(t_udf_list, func, nu, structure):
	for target in t_udf_list:
		print("Readin file = ", target)
		#
		data = read_and_calc(target)
		#
		save_data(data, target)
	return

#----- Read Data
def read_and_calc(target):
	if  target.split('_')[0] == 'Cycle':
		sim_type = target.split('_')[4]
	else:
		sim_type = target.split('_')[3]
	uobj = UDFManager(target)
	if sim_type == 'forward':
		uobj.jump(0)
		cell = uobj.get("Structure.Unit_Cell.Cell_Size")
		area_init = cell[0]*cell[1]
		z_init = cell[2]
		data = [[1.0, 0, 0, 0]]
	elif sim_type == 'backward':
		uobj.jump(1)
		vol = uobj.get("Statistics_Data.Volume.Batch_Average")
		area_init = vol**(2./3.)
		z_init = vol**(1./3.)
		data = []
	for i in range(1, uobj.totalRecord()):
		print("Reading Rec.=", i)
		uobj.jump(i)
		#
		cell = uobj.get("Structure.Unit_Cell.Cell_Size")
		#
		stress = uobj.get("Statistics_Data.Stress.Total.Batch_Average")
		t_stress = calc_stress(cell, stress, area_init)
		#
		bond_stress = uobj.get("Statistics_Data.Stress.Bond.Batch_Average")
		bond = calc_stress(cell, bond_stress, area_init)
		#
		non_bond_stress = uobj.get("Statistics_Data.Stress.Non_Bond.Batch_Average")
		non_bond = calc_stress(cell, non_bond_stress, area_init)
		#
		strain = uobj.get("Structure.Unit_Cell.Cell_Size.c")/z_init
		#
		temp = uobj.get("Statistics_Data.Temperature.Batch_Average")
		#
		data.append([strain, t_stress, non_bond, bond, temp])
	return data

#-----
def calc_stress(cell, stress, area_init):
	nom_stress = (cell[0]*cell[1])*(stress[2]-(stress[0] + stress[1])/2.)/area_init
	return nom_stress

#----- 計算結果をターゲットファイル名で保存
def save_data(data, target):

	name = target.split(".")[0]
	datafile = "SS_" + name + '.dat'
	with open(datafile,'w') as f:
		#
		f.write('#Strain\tNom Stress\tNon-Bond\tBond\tTemp\n\n')
		for line in data:
			for val in line:
				f.write(str(val) + '\t')
			f.write('\n')
	return

#----- 結果をプロット
def plot(func, nu, structure, target_list):
	plt_file = 'plot_Hyst.plt'
	make_script(plt_file, func, nu, structure, target_list)
	#
	if platform.system() == "Windows":
		subprocess.call([plt_file], shell=True)
	elif platform.system() == "Linux":
		subprocess.call(['gnuplot ' + plt_file], shell=True)
	return

# 必要なスクリプトを作成
def make_script(plt_file, func, nu, structure, target_list):
	script = script_content(func, nu, structure, target_list)
	with open(plt_file, 'w') as f:
		f.write(script)
	return

# スクリプトの中身
def script_content(func, nu, structure, target_list):
	script = 'set term pngcairo font "Arial,14"\n\n'
	script += '#set mono\nset colorsequence classic\n\n'
	script += 'set output "hysteresis.png"\n\n'
	script += 'set key left\nset size square\n'
	script += 'set xrange [1:]\nset yrange [0.:]\nset xtics 0.2\n#set ytics 0.01\n'
	script += 'set xlabel "Strain"\nset ylabel "Nominal Stress"\n\n'
	script += 'G=' + str(nu) + '\n'
	script += 'func = ' + str(func) + '\n'
	script += 'f(x,f) = f*G*(x -1./x**2.)\nf1 = (func - 1.)/(func + 1.)\nf2 = 1. - 2./func\n\n'
	script += 'plot	'
	lt = 1
	cycle = 0
	count = 0
	for target in target_list:
		if target.split('_')[1] == 'Cycle':
			if target.split('_')[2] == str(cycle) and target.split('_')[-2] == 'forward':
				script += '"' + str(target) + '" w l lw 2 lt ' + str(lt) + ' ti "cycle=' + str(target.split('_')[2]) + '", \\\n'
			elif target.split('_')[2] == str(cycle) and target.split('_')[-2] == 'backward':
				script += '"' + str(target) + '" w l lw 2 lt ' + str(lt) + ' noti, \\\n'
			count += 1
			if count > 1:
				lt += 1
				cycle += 1
				count = 0
	script += 'f(x,1) w l lw 2 lt 9 ti "Affin", \\\n'
	script += 'f(x,f2) w l lw 2 lt 8 ti "Phantom"'
	script += '\n\nreset'

	return script
