#!/usr/bin/env python
# -*- coding: utf-8 -*-
##### Import #####
from UDFManager import *

import argparse
import codecs
import os
import platform
import sys

import cognac_deform.values as val
##### Main #####
def deform():
	# 各種条件を読み取り
	read_all()
	# 
	setup()
	return

###################################
# 各種条件を読み取り
def read_all():
	read_arg()
	read_nw_cond()
	read_sim_cond()
	return

def read_arg():
	parser = argparse.ArgumentParser(description='Select udf file to read !')
	parser.add_argument('udf', help="udf file name to read previous simulation")
	args = parser.parse_args()
	if args.udf:
		if len(args.udf.split('.')) != 2 or args.udf.split('.')[1] != 'udf':
			print('\nthe file name you selected is not udf file !')
			sys.exit('select proper udf file to read.')
		elif not os.access(args.udf, os.R_OK):
			sys.exit('\nSelected udf of ', args.udf, ' seems not exist !\nbye now!!')
		else:
			val.read_udf = args.udf
			# print('Selected udf file is ' + val.read_udf)
	else:
		print('no udf file is selected')
		sys.exit('select proper udf file to read.')
	return

# 計算対象の条件を読み取る
def read_nw_cond():
	if not os.access('target_condition.udf', os.R_OK):
		sys.exit("\n'target_condition.udf' is not exists.")
	else:
		cond_u = UDFManager('target_condition.udf')
		val.func = cond_u.get('TargetCond.NetWork.N_Strands')
		val.nu = cond_u.get('TargetCond.System.Nu')
	return

# シミュレーション条件を設定する。
def read_sim_cond():
	if not os.path.isfile('../deform_condition.udf'):
		print('\nIn the parent directory, no "deform_condition.udf" is found !')
		print('New one will be generated.')
		print('Please, modify and save it !\n')
		make_newudf()
		input('Press ENTER to continue...')
	else:
		read_and_set()
	return

# make new udf when not found.
def make_newudf():
	contents = '''
	\\begin{def}
	CalcConditions:{
		Cognac_ver:select{"cognac112"} "使用する Cognac のバージョン",
		Cores: int "計算に使用するコア数を指定"
		} "Cognac による計算の条件を設定"
	SimpleDeformation:{
		DeformMode:select{"none", "Stretch", "Shear", "both"} "変形モードを選択",
			Stretch:{
				DeformRate[]:float "これらは変形レートのリスト",
				MaxDeformation:float "最大ひずみ",
				Resolution:float "これは１ステップ計算での伸長度　Res = lambda/1_step"
				}
			Shear:{
				DeformRate[]:float "これらは変形レートのリスト",
				MaxDeformation:float "最大ひずみ",
				Resolution:float "これは１ステップ計算での伸長度　Res = lambda/1_step"
				}
			both:{
				DeformRate[]:float "これらは変形レートのリスト",
				MaxDeformation:float "最大ひずみ",
				Resolution:float "これは１ステップ計算での伸長度　Res = lambda/1_step"
				}
		} "計算ターゲットの条件を設定"		
	CycleDeformation:{
		CyclicDeform:select{"none", "CyclicStretch", "CyclicShear"} "変形モードを選択",
		CyclicStretch:{
			StretchConditions[]:{
				MaxDeformation:float "最大ひずみ",
				Repeat:int "サイクルの繰り返し数",
				DeformRate[]:float "これらは変形レートのリスト",
				Resolution:float "これは１ステップ計算での伸長度　Res = lambda/1_step"
				}
			}
		CyclicShear:{
			ShearConditions[]:{
				MaxDeformation:float "最大ひずみ",
				Repeat:int "サイクルの繰り返し数",
				DeformRate[]:float "これらは変形レートのリスト",
				Resolution:float "これは１ステップ計算での伸長度　Res = lambda/1_step"
				}
			}
		} "計算ターゲットの条件を設定"
	\end{def}	

	\\begin{data}
	CalcConditions:{"cognac112",1}
	SimpleDeformation:{
		"both",
			{
			[1.0e-03,5.0e-4,1.0e-04,5.0e-05]
			3.00,
			1.0e-02
			}
			{
			[1.0e-03,5.0e-4,1.0e-04,5.0e-05]
			2.0,
			1.0e-02
			}
			{
			[1.0e-03,5.0e-4,1.0e-04,5.0e-05]
			3.00,
			1.0e-02
			}
		}
	CycleDeformation:{
		"CyclicShear",
			{
				[
					{2.0000000,
					3,
					[1.0000000e-03,1.0000000e-04]
					1.0000000e-02
					}
					{3.0000000,
					3,
					[1.0000000e-03,1.0000000e-04,1.0000000e-05]
					1.0000000e-02
					}
				]
			}
			{
				[
					{2.0000000,
					3,
					[1.0000000e-03,1.0000000e-04]
					1.0000000e-02
					}
					{3.0000000,
					3,
					[1.0000000e-03,1.0000000e-04,1.0000000e-05]
					1.0000000e-02
					}
				]
			}
		}
	\end{data}
	'''
	###
	with codecs.open('../deform_condition.udf', 'w', 'utf_8') as f:
		f.write(contents)
	return

# Read udf and setup initial conditions
def read_and_set():
	dic={'y':True,'yes':True,'q':False,'quit':False}
	while True:
		# read udf
		read_condition()
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
		return
	else:
		sys.exit("##### \nQuit !!")

# Read condition udf
def read_condition():
	u = UDFManager('../deform_condition.udf')
	u.jump(-1)
	# 使用するCognacのバージョン
	val.ver_Cognac = u.get('CalcConditions.Cognac_ver')
	# 計算に使用するコア数
	val.core = u.get('CalcConditions.Cores')
	# Simple Deformation
	val.simple_def_mode  = u.get('SimpleDeformation.DeformMode')
	if val.simple_def_mode == 'Stretch':
		val.sim_rate_list = u.get('SimpleDeformation.Stretch.DeformRate[]')
		val.sim_deform_max = u.get('SimpleDeformation.Stretch.MaxDeformation')
		val.sim_resolution = u.get('SimpleDeformation.Stretch.Resolution')
		val.sim_deform = val.simple_def_mode
	elif val.simple_def_mode == 'Shear':
		val.sim_rate_list = u.get('SimpleDeformation.Shear.DeformRate[]')
		val.sim_deform_max = u.get('SimpleDeformation.Shear.MaxDeformation')
		val.sim_resolution = u.get('SimpleDeformation.Shear.Resolution')
		val.sim_deform = val.simple_def_mode
	elif val.simple_def_mode == 'both':
		val.sim_rate_list = u.get('SimpleDeformation.both.DeformRate[]')
		val.sim_deform_max = u.get('SimpleDeformation.both.MaxDeformation')
		val.sim_resolution = u.get('SimpleDeformation.both.Resolution')
	# Cyclic Deformation
	tmp = []
	val.cyc_deform_max = []
	val.cyc_repeat = []
	val.cyc_ratelist = []
	val.cyc_resolution = []
	val.cyclic_deform = u.get('CycleDeformation.CyclicDeform')
	if val.cyclic_deform == 'CyclicStretch':
		tmp = u.get('CycleDeformation.CyclicStretch.StretchConditions[]')
	elif val.cyclic_deform == 'CyclicShear':
		tmp = u.get('CycleDeformation.CyclicShear.ShearConditions[]')
	for data in tmp:
		val.cyc_deform_max.append(data[0])
		val.cyc_repeat.append(data[1])
		val.cyc_ratelist.append(data[2])
		val.cyc_resolution.append(data[3])
	if val.simple_def_mode == 'none' and val.cyclic_deform == 'none':
		sys.exit('No proper condition is selected.\nBye!')
	return
# 
def init_calc():
	text = "################################################" + "\n"
	text += "Cores used for simulation\t\t" + str(val.core ) + "\n"
	text += "################################################" + "\n"
	if val.simple_def_mode != 'none':
		text += "Deform mode:\t\t\t\t" + str(val.simple_def_mode) + "\n"
		text += "Deform Rate:\t\t" + ', '.join(["{0:4.0e}".format(x) for x in val.sim_rate_list]) + "\n"
		text += "Maximum Strain:\t\t\t\t" + str(val.sim_deform_max) + "\n"
		text += "Resolution:\t\t\t\t" + str(round(val.sim_resolution,4)) + "\n"
		text += "################################################" + "\n"
	if val.cyclic_deform != 'none':
		text += "Deform mode:\t\t\t" + str(val.cyclic_deform) + "\n"
		for i in range(len(val.cyc_deform_max)):
			text += 'Cyclic condition #' + str(i) + '\n'
			text += "\tMaximum Strain:\t\t\t" + str(val.cyc_deform_max[i]) + "\n"
			text += "\tRepeat:\t\t\t\t" + str(val.cyc_repeat[i]) + "\n"
			text += "\tCyclic Deform Rate:\t" + ', '.join(["{0:4.0e}".format(x) for x in val.cyc_ratelist[i]]) + "\n"
			text += "\tResolution:\t\t\t" + str(round(val.cyc_resolution[i], 4)) + "\n"
		text += "################################################" + "\n"
	print(text)
	return














#######################################
#
def setup():
	print("\n\nSetting UP progress !!\n")
	if val.simple_def_mode != 'none':
		setup_simple_deform()
	elif val.cyclic_deform != 'none':
		setup_cyclic()
	return

#####
#
def setup_simple_deform():
	if val.simple_def_mode == 'both':
		for val.sim_deform in ['Shear', 'Stretch']:
			# 計算用のディレクトリーを作成
			set_dir()
			# ファイル名を設定し、バッチファイルを作成
			make_batch()
	else:
		# 計算用のディレクトリーを作成
		set_dir()
		# ファイル名を設定し、バッチファイルを作成
		make_batch()
	return
# 
def set_dir():
	val.calc_dir = val.sim_deform + '_calculation_read_' + val.read_udf.split('.')[0]
	if os.path.exists(val.calc_dir):
		print("Use existing dir of ", val.calc_dir)
	else:
		print("Make new dir of ", val.calc_dir)
		os.makedirs(val.calc_dir)
	#
	val.base_udf = os.path.join(val.calc_dir, 'base.udf')
	u = UDFManager(val.read_udf)
	u.jump(1)
	u.eraseRecord(record_pos=-999,record_num=-999)
	u.write(val.base_udf)
	return

# ファイル名を設定し、バッチファイルを作成
def make_batch():
	val.batch = "#!/bin/bash\n"
	#
	for rate in val.sim_rate_list:
		# UDFファイル名を設定
		rate_str = "{0:4.0e}".format(rate)
		if val.sim_deform == 'Stretch':
			uin = 'Stretch_rate_' + rate_str + "_uin.udf"
		elif val.sim_deform == 'Shear':
			uin = 'Shear_rate_' + rate_str + "_uin.udf"
		# 
		make_title("Calculating rate_" + rate_str)
		val.batch += val.ver_Cognac + ' -I ' + uin + ' -O ' + uin.replace("uin", "out") + ' -n ' + str(val.core) +' \n'
		val.batch += 'evaluate_simple_deform -f ' + str(val.func) + ' -n ' + str(val.nu) +'\n'
		udf_in =  os.path.join(val.calc_dir, uin)
		mod_udf(udf_in, rate)
	# バッチファイルを作成
	f_batch = os.path.join(val.calc_dir, '_deform.bat')
	with open(f_batch, 'w') as f:
		f.write(val.batch)
	if platform.system() == "Linux":
		os.chmod(f_batch, 0o777)
	return

# ターミナルのタイトルを設定
def make_title(title):
	if platform.system() == "Windows":
		val.batch += "title " + title + "\n"
	elif platform.system() == "Linux":
		val.batch += r'echo -ne "\033]0; ' + title + ' \007"' + '\n'
	return

#-----
def mod_udf(udf_in, rate):
	if val.sim_deform == 'Stretch':
		deform_time = (val.sim_deform_max - 1)/rate
	elif val.sim_deform == 'Shear':
		deform_time = val.sim_deform_max/rate
	#
	time_total = round(deform_time/val.sim_time_div)
	time_1_step = round(val.sim_resolution/val.sim_time_div/rate)
	#
	u = UDFManager(val.base_udf)
	# goto global data
	u.jump(-1)

	# Dynamics_Conditions
	p = 'Simulation_Conditions.Dynamics_Conditions.'
	u.put(100000.,		p + 'Max_Force')
	u.put(val.sim_time_div,	p + 'Time.delta_T')
	u.put(time_total,	p + 'Time.Total_Steps')
	u.put(time_1_step,	p + 'Time.Output_Interval_Steps')
	u.put(1.0,			p + 'Temperature.Temperature')
	u.put(0, 			p + 'Temperature.Interval_of_Scale_Temp')
	u.put(0,			p + 'Pressure_Stress.Pressure')

	# Deformation
	if val.sim_deform == 'Stretch':
		p = "Simulation_Conditions.Dynamics_Conditions.Deformation."
		u.put('Cell_Deformation', 		p + 'Method')
		u.put('Simple_Elongation', 		p + 'Cell_Deformation.Method')
		u.put('Initial_Strain_Rate', 	p + 'Cell_Deformation.Simple_Elongation.Input_Method')
		u.put(rate,	 					p + 'Cell_Deformation.Simple_Elongation.Initial_Strain_Rate.Rate')
		u.put(0.5, 						p + 'Cell_Deformation.Simple_Elongation.Poisson_Ratio')
		u.put('z', 						p + 'Cell_Deformation.Simple_Elongation.Axis')
		u.put(1, 						p + 'Cell_Deformation.Interval_of_Deform')
		u.put(0, 						p + 'Cell_Deformation.Deform_Atom')
	elif val.sim_deform == 'Shear':
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









#######
#
def setup_cyclic():
	val.batch = "#!/bin/bash\n"
	val.cyc_dir = val.cyclic_deform + '_read_' + val.read_udf.split('.')[0]
	if os.path.exists(val.cyc_dir):
		print("Use existing dir of ", val.cyc_dir)
	else:
		print("Make new dir of ", val.cyc_dir)
		os.makedirs(val.cyc_dir)
	#
	for id, val.cyc_def_max in enumerate(val.cyc_deform_max):
		for val.cyc_rate in val.cyc_ratelist[id]:
			set_cyclic_dir()
			make_cycle_batch(id)
			# バッチファイルを作成
			f_batch = os.path.join(val.calc_dir, '_deform.bat')
			with open(f_batch, 'w') as f:
				f.write(val.batch)
			if platform.system() == "Linux":
				os.chmod(f_batch, 0o777)
	batch_series()
	return

# 
def set_cyclic_dir():
	tmp_dir = 'Deform_until_' + str(val.cyc_def_max).replace('.', '_') + "_rate_" + "{0:4.0e}".format(val.cyc_rate)
	val.cyc_dirlist.append(tmp_dir)
	val.calc_dir = os.path.join(val.cyc_dir, tmp_dir)
	if os.path.exists(val.calc_dir):
		print("Use existing dir of ", val.calc_dir)
	else:
		print("Make new dir of ", val.calc_dir)
		os.makedirs(val.calc_dir)
	#
	val.base_udf = os.path.join(val.calc_dir, 'base.udf')
	u = UDFManager(val.read_udf)
	u.jump(1)
	val.system_size = float(u.get('Structure.Unit_Cell.Cell_Size.c'))
	u.eraseRecord(record_pos=-999,record_num=-999)
	u.write(val.base_udf)
	val.cyc_readudf = 'base.udf'
	return

# ファイル名を設定し、バッチファイルを作成
def make_cycle_batch(id):
	for val.cyc_count in range(val.cyc_repeat[id]):
		val.cyc_resol = val.cyc_resolution[id]
		make_cycle()

		val.batch += 'evaluate_cyclic_deform -f ' + str(val.func) + ' -n ' + str(val.nu) +'\n'	
	return

#
def make_cycle():
	for val.cyc_direction in ['_Forward', '_Backward']:
		make_title("Calculating_Cycle_until_" + str(val.cyc_def_max).replace('.', '_') + "_rate_" + "{0:4.0e}".format(val.cyc_rate)) + '_' + str(val.cyc_count)
		# UDFファイル名を設定
		uin = '#' +str(val.cyc_count) + val.cyc_direction + "_uin.udf"
		uout = uin.replace("uin", "out")
		val.batch += val.ver_Cognac + ' -I ' + uin + ' -O ' + uout + ' -n ' + str(val.core) +' \n'
		
		udf_in =  os.path.join(val.calc_dir, uin)
		mod_udf(udf_in)
		val.cyc_readudf = uout

	return

# ターミナルのタイトルを設定
def make_title(title):
	if platform.system() == "Windows":
		val.batch += "title " + title + "\n"
	elif platform.system() == "Linux":
		val.batch += r'echo -ne "\033]0; ' + title + ' \007"' + '\n'
	return

#-----
def mod_udf(udf_in):
	if val.cyclic_deform == 'CyclicStretch':
		deform_time = (def_max - 1)/rate
		speed = rate*val.system_size
	elif val.cyclic_deform == 'CyclicShear':
		deform_time = val.cyc_def_max/val.cyc_rate
	#
	time_total = round(deform_time/val.sim_time_div)
	time_1_step = round(resolution/val.sim_time_div/val.cyc_rate)
	#
	u = UDFManager(val.base_udf)
	# goto global data
	u.jump(-1)

	# Dynamics_Conditions
	p = 'Simulation_Conditions.Dynamics_Conditions.'
	u.put(100000.,		p + 'Max_Force')
	u.put(val.sim_time_div,	p + 'Time.delta_T')
	u.put(time_total,	p + 'Time.Total_Steps')
	u.put(time_1_step,	p + 'Time.Output_Interval_Steps')
	u.put(1.0,			p + 'Temperature.Temperature')
	u.put(0, 			p + 'Temperature.Interval_of_Scale_Temp')
	u.put(0,			p + 'Pressure_Stress.Pressure')

	# Deformation
	if val.cyclic_deform == 'CyclicStretch':
		p = "Simulation_Conditions.Dynamics_Conditions.Deformation."
		u.put('Cell_Deformation', 	p + 'Method')
		u.put('Simple_Elongation', 	p + 'Cell_Deformation.Method')
		u.put('Deformation_Speed', 	p + 'Cell_Deformation.Simple_Elongation.Input_Method')
		if val.cyc_direction == '_Forward':
			u.put(speed, p + 'Cell_Deformation.Simple_Elongation.Deformation_Speed.Speed')
		else:
			u.put(-1.*speed, p + 'Cell_Deformation.Simple_Elongation.Deformation_Speed.Speed')
		u.put(0.5, 						p + 'Cell_Deformation.Simple_Elongation.Poisson_Ratio')
		u.put('z', 						p + 'Cell_Deformation.Simple_Elongation.Axis')
		u.put(1, 						p + 'Cell_Deformation.Interval_of_Deform')
		u.put(0, 						p + 'Cell_Deformation.Deform_Atom')
	elif val.cyclic_deform == 'CyclicShear':
		p = "Simulation_Conditions.Dynamics_Conditions.Deformation."
		u.put('Lees_Edwards', 	p + 'Method')
		u.put('Steady', 		p + 'Lees_Edwards.Method')
		if val.cyc_direction == '_Forward':
			u.put(rate, 		p + 'Lees_Edwards.Steady.Shear_Rate')
		else:
			u.put(-1.*rate, 	p + 'Lees_Edwards.Steady.Shear_Rate')
	
	# Output_Flags
	u.put([1, 1, 1], 'Simulation_Conditions.Output_Flags.Structure')

	# Read_Set_of_Molecules
	p = 'Initial_Structure.Read_Set_of_Molecules'
	u.put(['', -1], p)

	# Generate_Method
	p = 'Initial_Structure.Generate_Method.'
	u.put('Restart', 		p + 'Method')
	u.put([val.cyc_readudf, -1, 1, 1], 	p + 'Restart')

	# Relaxation
	p = 'Initial_Structure.Relaxation.'
	u.put(0, p + 'Relaxation')
	#--- Write UDF ---
	u.write(udf_in)
	return


#######################################################################
# ファイル名を設定し、バッチファイルを作成
def batch_series():
	batch_series = ''
	for subdir in val.cyc_dirlist:
		if platform.system() == "Windows":
			batch_series += 'cd /d %~dp0\\' + subdir +'\n'
			batch_series += 'call _deform.bat\n'
		elif platform.system() == "Linux":
			batch_series += 'cd ./' + subdir +'\n'
			batch_series += './_deform.bat\n'
			batch_series += 'cd ../\n'
	if platform.system() == "Windows":
		batch_series += 'cd /d %~dp0\n'

	f_batch = os.path.join(val.cyc_dir, '_calc_all.bat')
	with open(f_batch, 'w') as f:
		f.write(batch_series)
		if platform.system() == "Linux":
			os.chmod(f_batch, 0o777)
	return