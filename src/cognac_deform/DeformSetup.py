#!/usr/bin/env python
# -*- coding: utf-8 -*-
##### Import #####
from UDFManager import *

import argparse
import codecs
import sys
import os
import shutil
import platform

import cognac_deform.values as val

##### Main #####
# 
def deform():
	read_all()
	make_base_udf()
	make_batch()
	return

############################################################################
##### Function #####
# 平衡計算したUDFファイルとその場所を選択
def read_all():
	read_arg()
	read_nw_cond()
	read_sim_cond()
	return

def read_arg():
	parser = argparse.ArgumentParser(description='Select udf file to read !')
	parser.add_argument("-f", "--file", help="udf file name to read previous simulation")
	args = parser.parse_args()
	if args.file:
		if len(args.file.split('.')) != 2 or args.file.split('.')[1] != 'udf':
			print('the file name you selected is not udf file !')
			sys.exit('select proper udf file to read.')
		elif not os.access(args.file, os.R_OK):
			sys.exit(args.file, 'seems not exist !')
		else:
			val.read_udf = args.file
			# print('Selected udf file is ' + val.read_udf)
	else:
		print('no udf file is selected')
		sys.exit('select proper udf file to read.')
	return

# 計算条件から、ホモポリマーとネットワークを判断し、chain_list を読み出す。
def read_nw_cond():
	# 計算対象の条件を読み取る
	if not os.access('target_condition.udf', os.R_OK):
		print("'target_condition.udf' is not exists.")
		exit(1)
	else:
		cond_u = UDFManager('target_condition.udf')
		val.func = cond_u.get('TargetCond.NetWork.N_Strands')
		val.nu = cond_u.get('TargetCond.System.Nu')
	return

# 
def read_sim_cond():
	#
	if not os.path.isfile('../deform_condition.udf'):
		print()
		print('In the parent directory, no "deform_condition.udf" is found !')
		print('New one will be generated.')
		print('Please, modify and save it !\n')
		makenewudf()
		input('Press ENTER to continue...')
	else:
		read_and_setcondition()
	return

###########################################
# make new udf when not found.
def makenewudf():
	contents = '''
	\\begin{def}
	CalcConditions:{
		Cognac_ver:select{"cognac112"} "使用する Cognac のバージョン",
		Cores: int "計算に使用するコア数を指定"
		} "Cognac による計算の条件を設定"
	SimulationConditions:{
		DeformMode:select{"Elong", "Shear"} "変形モードを選択",
		DeformRate[]:float "これらは変形レートのリスト",
		MaxDeformation:float "最大ひずみ",
		Resolution:float "これは１ステップ計算での伸長度　Res = lambda/1_step"
		} "計算ターゲットの条件を設定"
	\end{def}	

	\\begin{data}
	CalcConditions:{"cognac112",1}
	SimulationConditions:{
	"Elong",
	[1.0e-03,5.0e-03,1.0e-03,5.0e-04,1.0e-04,5.0e-05]
	3.0,
	1.0e-02
	}
	\end{data}
	'''
	###
	with codecs.open('../deform_condition.udf', 'w', 'utf_8') as f:
		f.write(contents)
	return

######################################
# Read udf and setup initial conditions
def read_and_setcondition():
	dic={'y':True,'yes':True,'q':False,'quit':False}
	while True:
		# read udf
		readconditionudf()
		# select
		init_calc()
		print('Change UDF: type [r]eload')
		print('Quit input process: type [q]uit')
		inp = input('Condition is OK ==> [y]es >> ').lower()
		if inp in dic:
			inp = dic[inp]
			break
		print('##### \nRead Condition UDF again \n#####\n\n')
	if inp:
		# 計算用のディレクトリーを作成
		# make_dir()
		print("\n\nSetting UP progress !!")
		return
	else:
		sys.exit("##### \nQuit !!")


####################################
# Read condition udf
def readconditionudf():
	u = UDFManager('../deform_condition.udf')
	u.jump(-1)
	##################
	# 使用するCognacのバージョン
	val.ver_Cognac = u.get('CalcConditions.Cognac_ver')
	# 計算に使用するコア数
	val.core = u.get('CalcConditions.Cores')
	#######################################################
	## 計算ターゲット
	val.def_mode  = u.get('SimulationConditions.DeformMode')
	val.rate_list = u.get('SimulationConditions.DeformRate[]')
	val.deform_max = u.get('SimulationConditions.MaxDeformation')
	val.resolution = u.get('SimulationConditions.Resolution')
	#
	val.calc_dir = val.def_mode + '_calculation'
	return

###############################################################
def init_calc():
	text = "################################################" + "\n"
	text += "Cores used for simulation\t\t" + str(val.core ) + "\n"
	text += "################################################" + "\n"
	text += "Deform mode:\t\t\t\t" + str(val.def_mode) + "\n"
	text += "Deform Rate:\t" + ', '.join(["{0:4.0e}".format(x) for x in val.rate_list]) + "\n"
	text += "Maximum Strain:\t\t\t\t" + str(val.deform_max) + "\n"
	text += "Resolution:\t\t\t\t" + str(round(val.resolution,4)) + "\n"
	text += "################################################" + "\n"
	print(text)
	return


# 
def make_base_udf():
	if os.path.exists(val.calc_dir):
		print("Use existing dir of ", val.calc_dir)
	else:
		print("Make new dir of ", val.calc_dir)
		os.makedirs(val.calc_dir)
	#
	val.base_udf = os.path.join(val.calc_dir, val.read_udf)
	print("Readin file = ", val.read_udf)
	u = UDFManager(val.read_udf)
	u.jump(1)
	u.eraseRecord(record_pos=-999,record_num=-999)
	u.write(val.base_udf)
	return

# ファイル名を設定し、バッチファイルを作成
def make_batch():
	val.batch = "#!/bin/bash\n"
	#
	for rate in val.rate_list:
		# UDFファイル名を設定
		rate_str = "{0:4.0e}".format(rate)
		if val.def_mode == 'Elong':
			uin = 'Elong_rate_' + rate_str + "_uin.udf"
		elif val.def_mode == 'Shear':
			uin = 'Shear_rate_' + rate_str + "_uin.udf"
		# 
		make_title("Calculating rate_" + rate_str)
		val.batch += val.ver_Cognac + ' -I ' + uin + ' -O ' + uin.replace("uin", "out") + ' -n ' + str(val.core) +' \n'
		val.batch += 'evaluate_simpledeform\n'
		udf_in =  os.path.join(val.calc_dir, uin)
		# shutil.copy(val.base_udf, udf_in)
		mod_udf(udf_in, rate)
	# バッチファイルを作成
	f_batch = os.path.join(val.calc_dir, '_deform.bat')
	with open(f_batch, 'w') as f:
		f.write(val.batch)
	if platform.system() == "Linux":
		os.chmod(f_batch, 0o777)
	return

###########################
# ターミナルのタイトルを設定
def make_title(title):
	if platform.system() == "Windows":
		val.batch += "title " + title + "\n"
	elif platform.system() == "Linux":
		val.batch += r'echo -ne "\033]0; ' + title + ' \007"' + '\n'
	return

#-----
def mod_udf(udf_in, rate):
	if val.def_mode == 'Elong':
		deform_time = (val.deform_max - 1)/rate
	elif val.def_mode == 'Shear':
		deform_time = val.deform_max/rate
	#
	time_total = round(deform_time/val.time_div)
	time_1_step = round(val.resolution/val.time_div/rate)
	#
	u = UDFManager(val.base_udf)
	# goto global data
	u.jump(-1)

	# Dynamics_Conditions
	p = 'Simulation_Conditions.Dynamics_Conditions.'
	u.put(100000.,		p + 'Max_Force')
	u.put(val.time_div,	p + 'Time.delta_T')
	u.put(time_total,	p + 'Time.Total_Steps')
	u.put(time_1_step,	p + 'Time.Output_Interval_Steps')
	u.put(1.0,			p + 'Temperature.Temperature')
	u.put(0, 			p + 'Temperature.Interval_of_Scale_Temp')
	u.put(0,			p + 'Pressure_Stress.Pressure')

	# Deformation
	if val.def_mode == 'Elong':
		p = "Simulation_Conditions.Dynamics_Conditions.Deformation."
		u.put('Cell_Deformation', 		p + 'Method')
		u.put('Simple_Elongation', 		p + 'Cell_Deformation.Method')
		u.put('Initial_Strain_Rate', 	p + 'Cell_Deformation.Simple_Elongation.Input_Method')
		u.put(rate,	 					p + 'Cell_Deformation.Simple_Elongation.Initial_Strain_Rate.Rate')
		u.put(0.5, 						p + 'Cell_Deformation.Simple_Elongation.Poisson_Ratio')
		u.put('z', 						p + 'Cell_Deformation.Simple_Elongation.Axis')
		u.put(1, 						p + 'Cell_Deformation.Interval_of_Deform')
		u.put(0, 						p + 'Cell_Deformation.Deform_Atom')
	elif val.def_mode == 'Shear':
		p = "Simulation_Conditions.Dynamics_Conditions.Deformation."
		u.put('Lees_Edwards', 	p + 'Method')
		u.put('Steady', 		p + 'Lees_Edwards.Method')
		u.put(rate, 			p + 'Lees_Edwards.Steady.Shear_Rate')
	
	# Output_Flags
	u.put([1, 1, 1], 'Simulation_Conditions.Output_Flags.Structure')

	# Read_Set_of_Molecules
	p = 'Initial_Structure.Read_Set_of_Molecules'
	u.put(['', -1], p)

	# Generate_Method
	p = 'Initial_Structure.Generate_Method.'
	u.put('Restart', 		p + 'Method')
	u.put(['', -1, 1, 1], 	p + 'Restart')

	# Relaxation
	p = 'Initial_Structure.Relaxation.'
	u.put(0, p + 'Relaxation')
	#--- Write UDF ---
	u.write(udf_in)
	return

