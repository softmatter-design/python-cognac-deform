#!/usr/bin/env python
# -*- coding: utf-8 -*-
##### Import #####
from UDFManager import *

import argparse
import codecs
import os
import platform
import sys

import cognac_deform.variables as var
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
			var.read_udf = args.udf
			# print('Selected udf file is ' + var.read_udf)
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
		var.func = cond_u.get('TargetCond.NetWork.N_Strands')
		var.nu = cond_u.get('TargetCond.System.Nu')
	return

# シミュレーション条件を設定する。
def read_sim_cond():
	while not os.path.isfile('../deform_condition.udf'):
		print('\nIn the parent directory, no "deform_condition.udf" is found !')
		print('New one will be generated.')
		print('Please, modify and save it !\n')
		make_newudf()
		input('Press ENTER to continue...')
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
	StepDeformation:{
		StepDeform:select{"none", "StepStretch", "StepShear"} "変形モードを選択",
		StepStretch:{
			StretchConditions:{
				Deformation:{
					MaxDeformation:float "最大ひずみ",
					DeformRate:float "変形レート",
					DeformSteps:int "シミュレーションのステップ数"
					}
				Relaxation[]:{
					RelaxationTime:int "緩和を観測する時間",
					ClacSteps:int "緩和時間の分割数",
					}
				}
			}
		StepShear:{
			ShearConditions:{
				Deformation:{
					MaxDeformation:float "最大ひずみ",
					DeformRate:float "変形レート",
					DeformSteps:int "シミュレーションのステップ数"
					}
				Relaxation[]:{
					RelaxationTime:int "緩和を観測する時間",
					CalcSteps:int "緩和時間の分割数",
					}
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
					{2.0,
					3,
					[1.0e-03,1.0e-04]
					1.0e-02
					}
					{3.0,
					3,
					[1.0e-03,1.00e-04,1.00e-05]
					1.00e-02
					}
				]
			}
			{
				[
					{2.00,
					3,
					[1.0e-03,1.00e-04]
					1.00e-02
					}
					{3.00,
					3,
					[1.00e-03,1.00e-04,1.00e-05]
					1.00e-02
					}
				]
			}
		}
	StepDeformation:{
		"StepStretch",
			{
				{
				{1.50,5.0e-02,100}
				[{100000,500}{100000,100}]
				}
			}
			{
				{
				{1.00,0.10,100}
				[{100000,500}{100000,100}]
				}
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
	var.ver_Cognac = u.get('CalcConditions.Cognac_ver')
	# 計算に使用するコア数
	var.core = u.get('CalcConditions.Cores')
	# Simple Deformation
	var.simple_def_mode  = u.get('SimpleDeformation.DeformMode').lower()
	if var.simple_def_mode == 'stretch':
		var.sim_rate_list = u.get('SimpleDeformation.Stretch.DeformRate[]')
		var.sim_deform_max = u.get('SimpleDeformation.Stretch.MaxDeformation')
		var.sim_resolution = u.get('SimpleDeformation.Stretch.Resolution')
		var.sim_deform = var.simple_def_mode
	elif var.simple_def_mode == 'shear':
		var.sim_rate_list = u.get('SimpleDeformation.Shear.DeformRate[]')
		var.sim_deform_max = u.get('SimpleDeformation.Shear.MaxDeformation')
		var.sim_resolution = u.get('SimpleDeformation.Shear.Resolution')
		var.sim_deform = var.simple_def_mode
	elif var.simple_def_mode == 'both':
		var.sim_rate_list = u.get('SimpleDeformation.both.DeformRate[]')
		var.sim_deform_max = u.get('SimpleDeformation.both.MaxDeformation')
		var.sim_resolution = u.get('SimpleDeformation.both.Resolution')
	# Cyclic Deformation
	tmp = []
	var.cyclic_deform = u.get('CycleDeformation.CyclicDeform')
	if var.cyclic_deform == 'CyclicStretch':
		tmp = u.get('CycleDeformation.CyclicStretch.StretchConditions[]')
	elif var.cyclic_deform == 'CyclicShear':
		tmp = u.get('CycleDeformation.CyclicShear.ShearConditions[]')
	for data in tmp:
		var.cyc_deform_max.append(data[0])
		var.cyc_repeat.append(data[1])
		var.cyc_ratelist.append(data[2])
		var.cyc_resolution.append(data[3])
	# Step Deformation
	var.step_deform = u.get('StepDeformation.StepDeform')
	if var.step_deform == 'StepShear':
		[var.step_deform_max, var.step_rate, var.step_steps] = u.get('StepDeformation.StepShear.ShearConditions.Deformation')
		deform_time = var.step_deform_max/var.step_rate
		#
		var.step_relaxation = u.get('StepDeformation.StepShear.ShearConditions.Relaxation[]')
	elif var.step_deform == 'StepStretch':
		[var.step_deform_max, var.step_rate, var.step_steps] = u.get('StepDeformation.StepStretch.StretchConditions.Deformation')
		deform_time = (var.step_deform_max - 1)/var.step_rate
		#
		var.step_relaxation = u.get('StepDeformation.StepStretch.StretchConditions.Relaxation[]')
	#
	dt = min(var.sim_time_div, deform_time/var.step_steps)	# dt の暫定値を決定
	total_steps = round(deform_time/dt)
	interval = max(1, round(total_steps/var.step_steps))	# 整数値の interval を決定
	dt = round(deform_time/var.step_steps/interval, 4)		# 小数点４桁で丸めたdtを決定
	var.step_deform_time = [dt, total_steps, interval]
	#
	if var.simple_def_mode == 'none' and var.cyclic_deform == 'none' and var.step_deform == 'none':
		sys.exit('No proper condition is selected.\nBye!')
	return
# 
def init_calc():
	text = "################################################" + "\n"
	text += "Cores used for simulation\t\t" + str(var.core ) + "\n"
	text += "################################################" + "\n"
	if var.simple_def_mode != 'none':
		text += "Deform mode:\t\t\t\t" + str(var.simple_def_mode) + "\n"
		text += "Deform Rate:\t\t" + ', '.join([f"{x:.1e}" for x in var.sim_rate_list]) + "\n"
		text += "Maximum Strain:\t\t\t\t" + str(var.sim_deform_max) + "\n"
		text += "Resolution:\t\t\t\t" + str(round(var.sim_resolution,4)) + "\n"
		text += "################################################" + "\n"
	if var.cyclic_deform != 'none':
		text += "Cyclic Deform mode:\t\t\t" + str(var.cyclic_deform) + "\n"
		for i in range(len(var.cyc_deform_max)):
			text += f'Cyclic condition #{i}\n'
			text += f"\tMaximum Strain:\t\t\t{var.cyc_deform_max[i]:.1f}\n"
			text += f"\tRepeat:\t\t\t\t{var.cyc_repeat[i]}\n"
			text += "\tCyclic Deform Rate:\t" + ', '.join([f"{x:.1e}" for x in var.cyc_ratelist[i]]) + "\n"
			text += "\tResolution:\t\t\t" + str(round(var.cyc_resolution[i], 4)) + "\n"
		text += "################################################" + "\n"
	if var.step_deform != 'none':
		text += f"Step Deform mode:\t\t\t{var.step_deform:}\n"
		text += f"Step Strain:\t\t\t\t{var.step_deform_max:.1f}\n"
		text += f"Deformation rate:\t\t\t{var.step_rate:.1e}\n"
		text += f"Deformation steps:\t\t\t{var.step_steps:}\n"
		text += f"Simulation time:\t\t{var.step_deform_time:}\n"
		text += "#\n"
		for i, data in enumerate(var.step_relaxation):
			text += f"Relaxation-{i:}\n"
			text += f"\tRelaxation Time:\t\t{data[0]:.1e}\n"
			text += f"\tCalc steps:\t\t\t{data[1]:}\n"
		text += "################################################" + "\n"
	print(text)
	return

#######################################
#
def setup():
	print("\n\nSetting UP progress !!\n")
	if var.simple_def_mode != 'none':
		setup_simple_deform()
	if var.cyclic_deform != 'none':
		setup_cyclic_deform()
	if var.step_deform != 'none':
		setup_step_deform()
	return

#####
#
def setup_simple_deform():
	if var.simple_def_mode == 'both':
		for var.sim_deform in ['shear', 'stretch']:
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
	var.calc_dir = var.sim_deform + '_calculation_read_' + var.read_udf.split('.')[0]
	if os.path.exists(var.calc_dir):
		print("Use existing dir of ", var.calc_dir)
	else:
		print("Make new dir of ", var.calc_dir)
		os.makedirs(var.calc_dir)
	#
	var.base_udf = os.path.join(var.calc_dir, 'base.udf')
	u = UDFManager(var.read_udf)
	u.jump(1)
	u.eraseRecord(record_pos=0, record_num=u.totalRecord()-1)
	u.write(var.base_udf)
	return

# ファイル名を設定し、バッチファイルを作成
def make_batch():
	var.batch = "#!/bin/bash\n"
	#
	for rate in var.sim_rate_list:
		# UDFファイル名を設定
		rate_str = "{0:4.0e}".format(rate)
		if var.sim_deform == 'stretch':
			uin = 'Stretch_rate_' + rate_str + "_uin.udf"
		elif var.sim_deform == 'shear':
			uin = 'Shear_rate_' + rate_str + "_uin.udf"
		# 
		make_title("Calculating rate_" + rate_str)
		var.batch += var.ver_Cognac + ' -I ' + uin + ' -O ' + uin.replace("uin", "out") + ' -n ' + str(var.core) +' \n'
		var.batch += 'evaluate_simple_deform -f ' + str(var.func) + ' -n ' + str(var.nu) +'\n'
		udf_in =  os.path.join(var.calc_dir, uin)
		make_simpledeform_udf(udf_in, rate)
	write_batchfile('_simpledeform.bat')
	return

#-----
def make_simpledeform_udf(udf_in, rate):
	if var.sim_deform == 'stretch':
		deform_time = (var.sim_deform_max - 1)/rate
	elif var.sim_deform == 'shear':
		deform_time = var.sim_deform_max/rate
	#
	time_total = round(deform_time/var.sim_time_div)
	time_1_step = round(var.sim_resolution/var.sim_time_div/rate)
	#
	u = UDFManager(var.base_udf)
	# goto global data
	u.jump(-1)
	# Dynamics_Conditions
	p = 'Simulation_Conditions.Dynamics_Conditions.'
	u.put(100000.,		p + 'Max_Force')
	u.put(var.sim_time_div,	p + 'Time.delta_T')
	u.put(time_total,	p + 'Time.Total_Steps')
	u.put(time_1_step,	p + 'Time.Output_Interval_Steps')
	u.put(1.0,			p + 'Temperature.Temperature')
	u.put(0, 			p + 'Temperature.Interval_of_Scale_Temp')
	u.put(0,			p + 'Pressure_Stress.Pressure')

	# Deformation
	if var.sim_deform == 'stretch':
		p = "Simulation_Conditions.Dynamics_Conditions.Deformation."
		u.put('Cell_Deformation', 		p + 'Method')
		u.put('Simple_Elongation', 		p + 'Cell_Deformation.Method')
		u.put('Initial_Strain_Rate', 	p + 'Cell_Deformation.Simple_Elongation.Input_Method')
		u.put(rate,	 					p + 'Cell_Deformation.Simple_Elongation.Initial_Strain_Rate.Rate')
		u.put(0.5, 						p + 'Cell_Deformation.Simple_Elongation.Poisson_Ratio')
		u.put('z', 						p + 'Cell_Deformation.Simple_Elongation.Axis')
		u.put(1, 						p + 'Cell_Deformation.Interval_of_Deform')
		u.put(0, 						p + 'Cell_Deformation.Deform_Atom')
	elif var.sim_deform == 'shear':
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
def setup_cyclic_deform():
	set_cyclic_basedir()
	#
	set_each_cycle()
	#
	batch_series()
	return

def set_cyclic_basedir():
	var.cyc_dir = var.cyclic_deform + '_read_' + var.read_udf.split('.')[0]
	if os.path.exists(var.cyc_dir):
		print("Use existing dir of ", var.cyc_dir)
	else:
		print("Make new dir of ", var.cyc_dir)
		os.makedirs(var.cyc_dir)
	return
#
def set_each_cycle():
	for id, var.cyc_def_max in enumerate(var.cyc_deform_max):
		for var.cyc_rate in var.cyc_ratelist[id]:
			var.batch = "#!/bin/bash\n"
			set_cyclic_dir()
			make_cycle_batch(id)
			# バッチファイルを作成
			write_batchfile('_cyclicdeform.bat')
	return
# 
def set_cyclic_dir():
	tmp_dir = 'Deform_until_' + str(var.cyc_def_max).replace('.', '_') + "_rate_" + f"{var.cyc_rate:.1e}".replace('.', '_')
	var.cyc_dirlist.append(tmp_dir)
	var.calc_dir = os.path.join(var.cyc_dir, tmp_dir)
	if os.path.exists(var.calc_dir):
		print("Use existing dir of ", var.calc_dir)
	else:
		print("Make new dir of ", var.calc_dir)
		os.makedirs(var.calc_dir)
	#
	var.base_udf = os.path.join(var.calc_dir, 'base.udf')
	u = UDFManager(var.read_udf)
	u.jump(1)
	var.system_size = float(u.get('Structure.Unit_Cell.Cell_Size.c'))
	u.eraseRecord(record_pos=0, record_num=u.totalRecord()-1)
	u.write(var.base_udf)
	var.cyc_readudf = 'base.udf'
	return

# ファイル名を設定し、バッチファイルを作成
def make_cycle_batch(id):
	for var.cyc_count in range(var.cyc_repeat[id]):
		var.cyc_resol = var.cyc_resolution[id]
		make_cycle()
		if var.cyclic_deform == 'CyclicStretch':
			var.batch += 'evaluate_cyclic_deform -f ' + str(var.func) + ' -n ' + str(var.nu) + ' -m stretch\n'
		elif var.cyclic_deform == 'CyclicShear':
			var.batch += 'evaluate_cyclic_deform -f ' + str(var.func) + ' -n ' + str(var.nu) + ' -m shear\n'
	return
#
def make_cycle():
	for var.cyc_direction in ['_Forward', '_Backward']:
		make_title("Calculating_Cycle_until_" + str(var.cyc_def_max).replace('.', '_') + "_rate_" + f"{var.cyc_rate:.1e}".replace('.','_') + '_#' + str(var.cyc_count) + var.cyc_direction)
		# UDFファイル名を設定
		uin = '#' +str(var.cyc_count) + var.cyc_direction + "_uin.udf"
		uout = uin.replace("uin", "out")
		var.batch += var.ver_Cognac + ' -I ' + uin + ' -O ' + uout + ' -n ' + str(var.core) +' \n'
		
		udf_in =  os.path.join(var.calc_dir, uin)
		mod_cycle_udf(udf_in)
		var.cyc_readudf = uout

	return

#-----
def mod_cycle_udf(udf_in):
	if var.cyclic_deform == 'CyclicStretch':
		deform_time = (var.cyc_def_max - 1)/var.cyc_rate
		speed = var.cyc_rate*var.system_size
	elif var.cyclic_deform == 'CyclicShear':
		deform_time = var.cyc_def_max/var.cyc_rate
	#
	time_total = round(deform_time/var.sim_time_div)
	time_1_step = round(var.cyc_resol/var.sim_time_div/var.cyc_rate)
	#
	u = UDFManager(var.base_udf)
	# goto global data
	u.jump(-1)
	# Dynamics_Conditions
	p = 'Simulation_Conditions.Dynamics_Conditions.'
	u.put(100000.,		p + 'Max_Force')
	u.put(var.sim_time_div,	p + 'Time.delta_T')
	u.put(time_total,	p + 'Time.Total_Steps')
	u.put(time_1_step,	p + 'Time.Output_Interval_Steps')
	u.put(1.0,			p + 'Temperature.Temperature')
	u.put(0, 			p + 'Temperature.Interval_of_Scale_Temp')
	u.put(0,			p + 'Pressure_Stress.Pressure')
	# Deformation
	if var.cyclic_deform == 'CyclicStretch':
		p = "Simulation_Conditions.Dynamics_Conditions.Deformation."
		u.put('Cell_Deformation', 	p + 'Method')
		u.put('Simple_Elongation', 	p + 'Cell_Deformation.Method')
		u.put('Deformation_Speed', 	p + 'Cell_Deformation.Simple_Elongation.Input_Method')
		if var.cyc_direction == '_Forward':
			u.put(speed, p + 'Cell_Deformation.Simple_Elongation.Deformation_Speed.Speed')
		else:
			u.put(-1.*speed, p + 'Cell_Deformation.Simple_Elongation.Deformation_Speed.Speed')
		u.put(0.5, 						p + 'Cell_Deformation.Simple_Elongation.Poisson_Ratio')
		u.put('z', 						p + 'Cell_Deformation.Simple_Elongation.Axis')
		u.put(1, 						p + 'Cell_Deformation.Interval_of_Deform')
		u.put(0, 						p + 'Cell_Deformation.Deform_Atom')
	elif var.cyclic_deform == 'CyclicShear':
		p = "Simulation_Conditions.Dynamics_Conditions.Deformation."
		u.put('Lees_Edwards', 	p + 'Method')
		u.put('Steady', 		p + 'Lees_Edwards.Method')
		if var.cyc_direction == '_Forward':
			u.put(var.cyc_rate, 		p + 'Lees_Edwards.Steady.Shear_Rate')
		else:
			u.put(-1.*var.cyc_rate, 	p + 'Lees_Edwards.Steady.Shear_Rate')
	# Output_Flags
	u.put([1, 1, 1], 'Simulation_Conditions.Output_Flags.Structure')
	# Read_Set_of_Molecules
	p = 'Initial_Structure.Read_Set_of_Molecules'
	u.put(['', -1], p)
	# Generate_Method
	p = 'Initial_Structure.Generate_Method.'
	u.put('Restart', 		p + 'Method')
	u.put([var.cyc_readudf, -1, 1, 1], 	p + 'Restart')
	# Relaxation
	p = 'Initial_Structure.Relaxation.'
	u.put(0, p + 'Relaxation')
	#--- Write UDF ---
	u.write(udf_in)
	return

#######################################
# ファイル名を設定し、バッチファイルを作成
def batch_series():
	batch_series = ''
	for subdir in var.cyc_dirlist:
		if platform.system() == "Windows":
			batch_series += 'cd /d %~dp0\\' + subdir +'\n'
			batch_series += 'call _deform.bat\n'
		elif platform.system() == "Linux":
			batch_series += 'cd ./' + subdir +'\n'
			batch_series += './_deform.bat\n'
			batch_series += 'cd ../\n'
	if platform.system() == "Windows":
		batch_series += 'cd /d %~dp0\n'

	f_batch = os.path.join(var.cyc_dir, '_calc_all.bat')
	with open(f_batch, 'w') as f:
		f.write(batch_series)
		if platform.system() == "Linux":
			os.chmod(f_batch, 0o777)
	return

#####
#
def setup_step_deform():
	# 計算用のディレクトリーを作成
	set_step_dir()
	# 
	make_step_batch()
	return
	
# 
def set_step_dir():
	var.calc_dir = f'{var.step_deform:}_read_{var.read_udf.split(".")[0]:}_until_' + f'{var.step_deform_max:.1f}'.replace('.','_')
	if os.path.exists(var.calc_dir):
		print("Use existing dir of ", var.calc_dir)
	else:
		print("Make new dir of ", var.calc_dir)
		os.makedirs(var.calc_dir)
	#
	var.base_udf = os.path.join(var.calc_dir, 'base.udf')
	u = UDFManager(var.read_udf)
	u.jump(1)
	u.eraseRecord(record_pos=0, record_num=u.totalRecord()-1)
	u.write(var.base_udf)
	return

# ファイル名を設定し、バッチファイルを作成
def make_step_batch():
	var.batch = "#!/bin/bash\n"
	# UDFファイル名を設定
	base = f'{var.step_deform}_until_' + f'{var.step_deform_max:.1e}'.replace('.', '_') + '_rate_' + f'{var.step_rate:.1e}'.replace('.', '_')
	uin = base + '_uin.udf'
	make_title(base)
	# 
	var.batch += var.ver_Cognac + ' -I ' + uin + ' -O ' + uin.replace("uin", "out") + ' -n ' + str(var.core) +' \n'
	var.batch += 'evaluate_step_deform ' + uin.replace("uin", "out") + f' -f {var.func} -n {var.nu} \n'
	udf_in =  os.path.join(var.calc_dir, uin)
	make_stepdeform_udf(udf_in)
	# バッチファイルを作成
	write_batchfile('_stepdeform.bat')
	return

#-----
def make_stepdeform_udf(udf_in):
	u = UDFManager(var.base_udf)
	# goto global data
	u.jump(-1)

	# Dynamics_Conditions
	p = 'Simulation_Conditions.Dynamics_Conditions.'
	u.put(100000.,		p + 'Max_Force')
	u.put(var.step_deform_time[0],	p + 'Time.delta_T')
	u.put(var.step_deform_time[1],	p + 'Time.Total_Steps')
	u.put(var.step_deform_time[2],	p + 'Time.Output_Interval_Steps')
	u.put(1.0,			p + 'Temperature.Temperature')
	u.put(0, 			p + 'Temperature.Interval_of_Scale_Temp')
	u.put(0,			p + 'Pressure_Stress.Pressure')

	# Deformation
	if var.step_deform == 'StepStretch':
		p = "Simulation_Conditions.Dynamics_Conditions.Deformation."
		u.put('Cell_Deformation', 		p + 'Method')
		u.put('Simple_Elongation', 		p + 'Cell_Deformation.Method')
		u.put('Initial_Strain_Rate', 	p + 'Cell_Deformation.Simple_Elongation.Input_Method')
		u.put(var.step_rate,	 					p + 'Cell_Deformation.Simple_Elongation.Initial_Strain_Rate.Rate')
		u.put(0.5, 						p + 'Cell_Deformation.Simple_Elongation.Poisson_Ratio')
		u.put('z', 						p + 'Cell_Deformation.Simple_Elongation.Axis')
		u.put(1, 						p + 'Cell_Deformation.Interval_of_Deform')
		u.put(0, 						p + 'Cell_Deformation.Deform_Atom')
	elif var.step_deform == 'StepShear':
		p = "Simulation_Conditions.Dynamics_Conditions.Deformation."
		u.put('Lees_Edwards', 	p + 'Method')
		u.put('Steady', 		p + 'Lees_Edwards.Method')
		u.put(var.step_rate, 			p + 'Lees_Edwards.Steady.Shear_Rate')
	
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





###########################################
# ターミナルのタイトルを設定
def make_title(title):
	if platform.system() == "Windows":
		var.batch += "title " + title + "\n"
	elif platform.system() == "Linux":
		var.batch += r'echo -ne "\033]0; ' + title + ' \007"' + '\n'
	return
#
def write_batchfile(filename):
	# バッチファイルを作成
	f_batch = os.path.join(var.calc_dir, filename)
	with open(f_batch, 'w') as f:
		f.write(var.batch)
	if platform.system() == "Linux":
		os.chmod(f_batch, 0o777)
	return


#################################################

# アトムのポジションを回転
def rotate_position(u, axis):
	R = rotate(axis, np.pi/2.)
	u.jump(u.totalRecord() - 1)
	pos = u.get('Structure.Position.mol[].atom[]')
	for i, mol in enumerate(pos):
		for j, atom in enumerate(mol):
			tmp = list(np.array(R).dot(np.array(atom)))
			u.put(tmp, 'Structure.Position.mol[].atom[]', [i, j])
	return

def rotate(axis, deg):
	if axis == 'x':
		R = [
			[1., 0., 0.],
			[0., np.cos(deg), -1*np.sin(deg)],
			[0., np.sin(deg), np.cos(deg)]
		]
	elif axis == 'y':
		R = [
			[np.cos(deg), 0., np.sin(deg)],
			[0., 1., 0.],
			[-1*np.sin(deg), 0., np.cos(deg)]
		]
	elif axis == 'z':
		R = [
			[np.cos(deg), -1*np.sin(deg), 0.],
			[np.sin(deg), np.cos(deg), 0.],
			[0., 0., 1.]
		]
	return R