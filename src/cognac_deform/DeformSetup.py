#!/usr/bin/env python
# -*- coding: utf-8 -*-
##### Import #####
from UDFManager import *

import argparse
import codecs
import numpy as np
import os
import platform
import sys
import uuid

import cognac_deform.variables as var
################
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
	if os.path.isfile('deform_condition.udf'):
		var.deform_udf = 'deform_condition.udf'
		read_and_set()
	else:
		while not os.path.isfile('../deform_condition.udf'):
			print('\nIn the parent directory, no "deform_condition.udf" is found !')
			print('New one will be generated.')
			print('Please, modify and save it !\n')
			make_newudf()
			input('Press ENTER to continue...')
		var.deform_udf = '../deform_condition.udf'
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
					CalcSteps:int "緩和時間の分割数",
					}
				Repeat[]:{
					Repeat:int "繰り返し数",
					RelaxationTime:int "緩和を観測する時間",
					CalcSteps:int "緩和時間の分割数",
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
				Repeat[]:{
					Repeat:int "繰り返し数",
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
				{1.50,5.0e-02,200}
				[{100000,500}{100000,100}]
				[{3,1000000,500}]
				}
			}
			{
				{
				{1.00,0.10,200}
				[{100000,500}{100000,100}]
				[{3,1000000,500}]
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
	u = UDFManager(var.deform_udf)
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
		max_strain, repeat, ratelist, resolution = data
		var.cyc_deform_cond_dic[max_strain] = [repeat, ratelist, resolution]
		# var.cyc_deform_max_list.append(data[0])
		# var.cyc_repeat.append(data[1])
		# var.cyc_ratelist.append(data[2])
		# var.cyc_resolution.append(data[3])
	# Step Deformation
	var.step_deform = u.get('StepDeformation.StepDeform')
	if var.step_deform == 'StepShear':
		[var.step_deform_max, var.step_rate, var.step_steps] = u.get('StepDeformation.StepShear.ShearConditions.Deformation')
		deform_time = var.step_deform_max/var.step_rate
		#
		var.step_relaxation = u.get('StepDeformation.StepShear.ShearConditions.Relaxation[]')
		var.step_repeat = u.get('StepDeformation.StepShear.ShearConditions.Repeat[]')[0]
	elif var.step_deform == 'StepStretch':
		[var.step_deform_max, var.step_rate, var.step_steps] = u.get('StepDeformation.StepStretch.StretchConditions.Deformation')
		if var.step_deform_max == 1.0:
			sys.exit('\nStep Stretch Condition is not proper !!\nMax Deformation should be greater than 1.0 !')
		else:
			deform_time = abs(var.step_deform_max - 1)/var.step_rate
		#
		var.step_relaxation = u.get('StepDeformation.StepStretch.StretchConditions.Relaxation[]')
		var.step_repeat = u.get('StepDeformation.StepShear.ShearConditions.Repeat[]')[0]
	#
	if var.step_deform != 'none':
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
		count = 0
		for key in var.cyc_deform_cond_dic:
			text += f'Cyclic condition #{count}\n'
			text += f"\tMaximum Strain:\t\t\t{key:.1f}\n"
			text += f"\tRepeat:\t\t\t\t{var.cyc_deform_cond_dic[key][0]}\n"
			text += "\tCyclic Deform Rate:\t" + ', '.join([f"{x:.1e}" for x in var.cyc_deform_cond_dic[key][1]]) + "\n"
			text += "\tResolution:\t\t\t" + str(round(var.cyc_deform_cond_dic[key][2], 4)) + "\n"
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
			text += f"\tCalc. steps:\t\t\t{data[1]:}\n"
		text += "#\n"
		text += f'Repeat:\t\t\t\t\t{var.step_repeat[0]:}\n'
		text += f'Relaxation steps:\t\t\t{var.step_repeat[1]:.1e}\n'
		text += f'Calc. Steps:\t\t\t\t{var.step_repeat[2]:}\n'
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
# 単純変形の設定
def setup_simple_deform():
	if var.simple_def_mode == 'both':
		for var.sim_deform in ['shear', 'stretch']:
			set_simple_eachrate()
	else:
		set_simple_eachrate()
	return


def set_simple_eachrate():
	var.sim_basedir = f"{var.sim_deform:}_calculation_read_{var.read_udf.split('.')[0]:}_until_{var.sim_deform_max:}"
	if os.path.exists(var.sim_basedir):
		print("Use existing dir of ", var.sim_basedir)
	else:
		print("Make new dir of ", var.sim_basedir)
		os.makedirs(var.sim_basedir)

	c_dir = os.getcwd().split('\\')[-1]
	var.title_base = str(c_dir.split('_', 2)[-1]) + f"_{var.sim_deform:}_calculation_until_{var.sim_deform_max:}_"
	# プラットフォームに応じて命令を変更
	if platform.system() == "Windows":
		task = 'call calc_all.bat\n'
		filename = 'calc_all.bat'
	elif platform.system() == "Linux":
		task = 'sh calc_all.sh\n'
		filename = 'calc_all.sh'
		#
		task2 = 'sh eval_all.sh\n'
		filename2 = 'eval_all.sh'
		option = f'simple_deform.py -f {str(var.func):} -n {str(var.nu):} -m {var.sim_deform:} -s \n'
		make_batch_series([f'rate_{rate:4.0e}' for rate in var.sim_rate_list], var.sim_basedir, task2, filename2, option)
	make_batch_series([f'rate_{rate:4.0e}' for rate in var.sim_rate_list], var.sim_basedir, task, filename,'')

	for var.sim_rate in var.sim_rate_list:
		var.sim_ratedir = os.path.join(var.sim_basedir, f"rate_{var.sim_rate:4.0e}")
		#
		if os.path.exists(var.sim_ratedir):
			print("Use existing dir of ", var.sim_ratedir)
		else:
			print("Make new dir of ", var.sim_ratedir)
			os.makedirs(var.sim_ratedir)
		#
		set_rotation_simple()
	return

def set_rotation_simple():
	# 変形方法に応じて回転方向を設定
	if var.sim_deform == 'shear':
		var.step_rotate = ['base', 'x', 'y', 'z', 'yx', 'zx']
	elif var.sim_deform == 'stretch':
		var.step_rotate = ['base', 'x', 'y']
	# プラットフォームに応じて命令を変更
	if platform.system() == "Windows":
		task = 'calc.bat\n'
		filename = 'calc_all.bat'
		option = f'evaluate_simple_deform -f {str(var.func):} -n {str(var.nu):} -m {var.sim_deform:} -a \n'
	elif platform.system() == "Linux":
		task = 'pjsub calc.sh\n'
		filename = 'calc_all.sh'
		option = ''
		#
		task2 = 'sh eval.sh\n'
		filename2 = 'eval_all.sh'
		option2 = f'simple_deform.py -f {str(var.func):} -n {str(var.nu):} -m {var.sim_deform:} -a \n'
		make_batch_series(['rotate_' + dir for dir in var.step_rotate], var.sim_ratedir, task2, filename2, option2)
	make_batch_series(['rotate_' + dir for dir in var.step_rotate], var.sim_ratedir, task, filename, option)

	for rotate in var.step_rotate:
		set_rotate_dir_sim(rotate)
		set_udf_batch_sim()
	return

def set_rotate_dir_sim(rotate):
	tmp_dir = f'rotate_{rotate}'
	var.title_name = var.title_base + f"rate_{var.sim_rate:4.0e}" + f'_rotate_{rotate}'
	var.sim_dirlist.append(tmp_dir)
	var.calc_dir = os.path.join(var.sim_ratedir, tmp_dir)
	if os.path.exists(var.calc_dir):
		print("Use existing dir of ", var.calc_dir)
	else:
		print("Make new dir of ", var.calc_dir)
		os.makedirs(var.calc_dir)

	var.base_udf = os.path.join(var.calc_dir, 'base.udf')
	u = UDFManager(var.read_udf)
	u.jump(1)
	u.eraseRecord(record_pos=0, record_num=u.totalRecord()-1)
	if rotate != 'base':
		rotate_position(u, rotate)
	u.write(var.base_udf)
	return

# ファイル名を設定し、バッチファイルを作成
def set_udf_batch_sim():
	# UDFファイル名を設定
	uin = f'rate_{var.sim_rate:4.0e}_uin.udf'
	# プラットフォームに応じてバッチファイルを設定
	if platform.system() == "Windows":
		make_title(var.title_name)
		var.batch = "#!/bin/bash\n"
		target_bat = 'calc.bat'
		var.batch += var.ver_Cognac + ' -I ' + uin + ' -O ' + uin.replace("uin", "out") + ' -n ' + str(var.core) +' \n'
		var.batch += f'evaluate_simple_deform -f {str(var.func):} -n {str(var.nu):} -m {var.sim_deform:} \n'
	elif platform.system() == "Linux":
		target_bat = 'calc.sh'
		var.batch = '#PJM -L "node=1"\n'
		var.batch += '#PJM -L "rscgrp=small"\n'
		var.batch += '#PJM -L "elapse=72:00:00"\n'
		var.batch += '#PJM -g hp220245\n'
		var.batch += '#PJM -x PJM_LILO_GFSCACHE=/vol0004\n'
		var.batch += '#PJM -S\n'
		var.batch += 'export UDF_DEF_PATH="/vol0400/data/hp220245/octa/OCTA84/ENGINES/udf"\n'
		var.batch += 'COGNAC="/vol0400/data/hp220245/octa/OCTA84/ENGINES/bin/unknown/cognac112"\n\n'
		var.batch += '${COGNAC} -I ' + uin + ' -O' + uin.replace("uin", "out") + ' -n 48 \n'
		#
		eval = '#!/bin/sh\n'
		eval += f'simple_deform.py -f {str(var.func):} -n {str(var.nu):} -m {var.sim_deform:} \n'
		write_batchfile(var.calc_dir, 'eval.sh', eval)
	write_batchfile(var.calc_dir, target_bat, var.batch)

	udf_in =  os.path.join(var.calc_dir, uin)
	make_simpledeform_udf(udf_in)
	return

#-----
def make_simpledeform_udf(udf_in):
	if var.sim_deform == 'stretch':
		deform_time = abs(var.sim_deform_max - 1)/var.sim_rate
	elif var.sim_deform == 'shear':
		deform_time = var.sim_deform_max/var.sim_rate
	#
	time_total = round(deform_time/var.sim_time_div)
	time_1_step = round(var.sim_resolution/var.sim_time_div/var.sim_rate)
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
		if var.sim_deform_max < 1.:
			var.sim_rate = -1*var.sim_rate
		u.put(var.sim_rate,	 					p + 'Cell_Deformation.Simple_Elongation.Initial_Strain_Rate.Rate')
		u.put(0.5, 						p + 'Cell_Deformation.Simple_Elongation.Poisson_Ratio')
		u.put('z', 						p + 'Cell_Deformation.Simple_Elongation.Axis')
		u.put(1, 						p + 'Cell_Deformation.Interval_of_Deform')
		u.put(0, 						p + 'Cell_Deformation.Deform_Atom')
	elif var.sim_deform == 'shear':
		p = "Simulation_Conditions.Dynamics_Conditions.Deformation."
		u.put('Lees_Edwards', 	p + 'Method')
		u.put('Steady', 		p + 'Lees_Edwards.Method')
		u.put(var.sim_rate, 			p + 'Lees_Edwards.Steady.Shear_Rate')
	
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
# 繰り返し変形の設定
def setup_cyclic_deform():
	set_cyclic_basedir()
	set_each_cycle()
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
	for cyc_def_max in var.cyc_deform_cond_dic:
		for cyc_rate in var.cyc_deform_cond_dic[cyc_def_max][1]:
			cond_dir = 'Deform_until_' + str(cyc_def_max).replace('.', '_') + "_rate_" + f"{cyc_rate:.1e}".replace('.', '_')
			var.cyc_dirlist.append(cond_dir)
			middle_dir = os.path.join(var.cyc_dir, cond_dir)
			if os.path.exists(middle_dir):
				print("Use existing dir of ", middle_dir)
			else:
				print("Make new dir of ", middle_dir)
				os.makedirs(middle_dir)
			set_cyclic_rotation(middle_dir, cyc_def_max, cyc_rate)
	# プラットフォームに応じて命令を変更
	if platform.system() == "Windows":
		task = 'call calc_all.bat\n'
		filename = 'calc_all.bat'
	elif platform.system() == "Linux":
		task = 'sh calc_all.sh\n'
		filename = 'calc_all.sh'
		#
		task2 = 'sh eval_all.sh\n'
		filename2 = 'eval_all.sh'
		make_batch_series(var.cyc_dirlist, var.cyc_dir, task2, filename2,'')
	make_batch_series(var.cyc_dirlist, var.cyc_dir, task, filename,'')
	return

def set_cyclic_rotation(middle_dir, cyc_def_max, cyc_rate):
	if var.cyclic_deform == 'CyclicShear':
		var.cyc_rotate = ['base', 'x', 'y', 'z', 'yx', 'zx']
		deform = 'shear'
	elif var.cyclic_deform == 'CyclicStretch':
		var.cyc_rotate = ['base', 'x', 'y']
		deform = 'stretch'
	for rotate in var.cyc_rotate:
		set_cyc_rotate_dir(middle_dir, rotate, cyc_def_max, cyc_rate)
	# プラットフォームに応じて命令を変更
	if platform.system() == "Windows":
		task = 'call calc.bat\n'
		filename = 'calc_all.bat'
		option = f'evaluate_cyclic_deform -f {str(var.func):} -n {str(var.nu):} -m {deform:} -a \n'
	elif platform.system() == "Linux":
		task = 'sh calc.sh\n'
		filename = 'calc_all.sh'
		option = ''
		# 評価用のバッチを作成
		task2 = 'sh eval.sh\n'
		filename2 = 'eval_all.sh'
		option2 = f'cyclic_deform.py -f {str(var.func):} -n {str(var.nu):} -m {deform:} -a \n'
		make_batch_series(['rotate_' + dir for dir in var.cyc_rotate], middle_dir, task2, filename2, option2)
	make_batch_series(['rotate_' + dir for dir in var.cyc_rotate], middle_dir, task, filename, option)
	return

def set_cyc_rotate_dir(middle_dir, rotate, cyc_def_max, cyc_rate):
	tmp_dir = f'rotate_{rotate}'
	var.calc_dir = os.path.join(middle_dir, tmp_dir)
	if os.path.exists(var.calc_dir):
		print("Use existing dir of ", var.calc_dir)
	else:
		print("Make new dir of ", var.calc_dir)
		os.makedirs(var.calc_dir)
	var.base_udf = os.path.join(var.calc_dir, 'base.udf')
	u = UDFManager(var.read_udf)
	u.jump(1)
	u.eraseRecord(record_pos=0, record_num=u.totalRecord()-1)
	if rotate != 'base':
		rotate_position(u, rotate)
	u.write(var.base_udf)

	make_cycle_batch(cyc_def_max, cyc_rate, rotate)

	return

# ファイル名を設定し、バッチファイルを作成
def make_cycle_batch(cyc_def_max, cyc_rate, rotate):
	repeatcount = ''
	calc_all = "#!/bin/bash\n"
	jobname = 'name' + str(uuid.uuid4())
	var.batch = "#!/bin/bash\n"
	for var.cyc_count in range(var.cyc_deform_cond_dic[cyc_def_max][0]):
		var.cyc_resol = var.cyc_deform_cond_dic[cyc_def_max][2]
		calc_all = make_cycle(cyc_def_max, cyc_rate, rotate, calc_all, jobname)
		repeatcount += str(var.cyc_count) + ' '
		if platform.system() == "Windows":
			if var.cyclic_deform == 'CyclicStretch':
				var.batch += 'evaluate_cyclic_deform -f ' + str(var.func) + ' -n ' + str(var.nu) + ' -m stretch\n'
			elif var.cyclic_deform == 'CyclicShear':
				var.batch += 'evaluate_cyclic_deform -f ' + str(var.func) + ' -n ' + str(var.nu) + ' -m shear\n'
			
			# バッチファイルを作成
			write_batchfile(var.calc_dir, 'calc.bat', var.batch)
	#
	if platform.system() == "Linux":
		evaluate = '#!/bin/sh\n'
		evaluate += 'cyclic_deform.py -f ' + str(var.func) + ' -n ' + str(var.nu) + ' -m shear\n'
		write_batchfile(var.calc_dir, 'eval.sh', evaluate)
		write_batchfile(var.calc_dir, 'calc.sh', calc_all)

	return
#
def make_cycle(cyc_def_max, cyc_rate, rotate, calc_all, jobname):
	for var.cyc_direction in ['_Forward', '_Backward']:
		# UDFファイル名を設定
		uin = 'No_' +str(var.cyc_count) + var.cyc_direction + "_uin.udf"
		uout = uin.replace("uin", "out")
		if platform.system() == "Windows":
			make_title(var.title_name + "_Calculating_Cycle_until_" + str(cyc_def_max).replace('.', '_') + "_rate_" + f"{cyc_rate:.1e}".replace('.','_') + '_No' + str(var.cyc_count) + var.cyc_direction)
			var.batch += var.ver_Cognac + ' -I ' + uin + ' -O ' + uout + ' -n ' + str(var.core) +' \n'
		elif platform.system() == "Linux":
			calc_sh = '#PJM -L "node=1"\n'
			calc_sh += '#PJM -L "rscgrp=small"\n'
			calc_sh += '#PJM -L "elapse=72:00:00"\n'
			calc_sh += '#PJM -g hp220245\n'
			calc_sh += '#PJM -x PJM_LILO_GFSCACHE=/vol0004\n'
			calc_sh += '#PJM -S\n'
			calc_sh += 'export UDF_DEF_PATH="/vol0400/data/hp220245/octa/OCTA84/ENGINES/udf"\n'
			calc_sh += 'COGNAC="/vol0400/data/hp220245/octa/OCTA84/ENGINES/bin/unknown/cognac112"\n\n'
			calc_sh += '${COGNAC} -I ' + uin + ' -O' + uout + ' -n 48 \n'
			# バッチファイルを作成
			write_batchfile(var.calc_dir, 'No_' + str(var.cyc_count) + var.cyc_direction + ".sh", calc_sh)
			#
			calc_all += f'pjsub --step --sparam "jnam={jobname:}" No_{var.cyc_count:}{var.cyc_direction:}.sh\n'
		udf_in =  os.path.join(var.calc_dir, uin)
		if var.cyc_count == 0 and var.cyc_direction == '_Forward':
			var.cyc_readudf = 'base.udf'
		mod_cycle_udf(cyc_def_max, cyc_rate, udf_in)
		var.cyc_readudf = uout
	return calc_all

#-----
def mod_cycle_udf(cyc_def_max, cyc_rate, udf_in):
	if var.cyclic_deform == 'CyclicStretch':
		deform_time = (cyc_def_max - 1)/cyc_rate
		speed = cyc_rate*var.system_size
	elif var.cyclic_deform == 'CyclicShear':
		deform_time = cyc_def_max/cyc_rate
	#
	time_total = round(deform_time/var.sim_time_div)
	time_1_step = round(var.cyc_resol/var.sim_time_div/cyc_rate)
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
			u.put(cyc_rate, 		p + 'Lees_Edwards.Steady.Shear_Rate')
		else:
			u.put(-1.*cyc_rate, 	p + 'Lees_Edwards.Steady.Shear_Rate')
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



#####
#
def setup_step_deform():
	# 計算用のディレクトリーを作成
	set_step_basedir()
	# 
	set_rotation_step()
	
	return
	
# 
def set_step_basedir():
	var.step_dir = f'{var.step_deform:}_until_' + f'{var.step_deform_max:.1f}'.replace('.','_') + '_rate_' + f'{var.step_rate:.1e}'.replace('.', '_') + f'_read_{var.read_udf.split(".")[0]:}'

	if os.path.exists(var.step_dir):
		print("Use existing dir of ", var.step_dir)
	else:
		print("Make new dir of ", var.step_dir)
		os.makedirs(var.step_dir)
	return

def set_rotation_step():
	if var.step_deform == 'StepShear':
		var.step_rotate = ['base', 'x', 'y', 'z', 'yx', 'zx']
	elif var.step_deform == 'StepStretch':
		var.step_rotate = ['base', 'x', 'y']
	for rotate in var.step_rotate:
		set_rotate_dir(rotate)
		set_udf_batch(rotate)
	#
	if platform.system() == "Windows":
		task = 'call calc_all.bat\n'
		filename = 'calc_all.bat'
		#
		if var.step_deform == 'StepStretch':
			option = f'evaluate_step_deform -f {var.func} -n {var.nu} -m stretch -a\n'
		elif var.step_deform == 'StepShear':
			option = f'evaluate_step_deform -f {var.func} -n {var.nu} -m shear -a\n'
	elif platform.system() == "Linux":
		task = 'sh calc_all.sh &\n'
		filename = 'calc_all.sh'
		option = ''
		#
		task2 = 'sh eval.sh\n'
		filename2 = 'eval_all.sh'
		if var.step_deform == 'StepStretch':
			option2 = f'step_deform.py -f {var.func} -n {var.nu} -m stretch -a\n'
		elif var.step_deform == 'StepShear':
			option2 = f'step_deform.py -f {var.func} -n {var.nu} -m shear -a\n'
		make_batch_series(var.step_dirlist, var.step_dir, task2, filename2, option2)
	
	make_batch_series(var.step_dirlist, var.step_dir, task, filename, option)
	return

def set_rotate_dir(rotate):
	tmp_dir = f'rotate_{rotate}'
	var.step_dirlist.append(tmp_dir)
	var.calc_dir = os.path.join(var.step_dir, tmp_dir)
	if os.path.exists(var.calc_dir):
		print("Use existing dir of ", var.calc_dir)
	else:
		print("Make new dir of ", var.calc_dir)
		os.makedirs(var.calc_dir)
	var.base_udf = os.path.join(var.calc_dir, 'base.udf')
	u = UDFManager(var.read_udf)
	u.jump(1)
	u.eraseRecord(record_pos=0, record_num=u.totalRecord()-1)
	if rotate != 'base':
		rotate_position(u, rotate)
	u.write(var.base_udf)
	return

# アトムのポジションを回転
def rotate_position(u, axis):
	R = rotate(axis, np.pi/2.)
	u.jump(u.totalRecord() - 1)
	pos = u.get('Structure.Position.mol[].atom[]')
	for i, mol in enumerate(pos):
		for j, atom in enumerate(mol):
			tmp = list(np.dot(np.array(R), np.array(atom)))
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
	elif axis == 'yx':
		Ry = [
			[np.cos(deg), 0., np.sin(deg)],
			[0., 1., 0.],
			[-1*np.sin(deg), 0., np.cos(deg)]
		]
		Rx = [
			[1., 0., 0.],
			[0., np.cos(deg), -1*np.sin(deg)],
			[0., np.sin(deg), np.cos(deg)]
		]
		R = list(np.dot(np.array(Rx), np.array(Ry)))
	elif axis == 'zx':
		Rz = [
			[np.cos(deg), -1*np.sin(deg), 0.],
			[np.sin(deg), np.cos(deg), 0.],
			[0., 0., 1.]
		]
		Rx = [
			[1., 0., 0.],
			[0., np.cos(deg), -1*np.sin(deg)],
			[0., np.sin(deg), np.cos(deg)]
		]
		R = list(np.dot(np.array(Rx), np.array(Rz)))
	return R

def set_udf_batch(rotate):
	# UDFファイル名を設定
	base = f'{var.step_deform}_until_' + f'{var.step_deform_max:.1e}'.replace('.', '_') + '_rate_' + f'{var.step_rate:.1e}'.replace('.', '_') + f'_{rotate}'
	#
	uin = 'deform_uin.udf'
	uout = uin.replace("uin", "out")
	if platform.system() == "Windows":
		make_title(var.title_name + '_' + base + "_deform")
		var.batch = "#!/bin/bash\n"
		var.batch += var.ver_Cognac + ' -I ' + uin + ' -O ' + uout + ' -n ' + str(var.core) +' \n'
	elif platform.system() == "Linux":
		calc_sh = '#PJM -L "node=1"\n'
		calc_sh += '#PJM -L "rscgrp=small"\n'
		calc_sh += '#PJM -L "elapse=72:00:00"\n'
		calc_sh += '#PJM -g hp220245\n'
		calc_sh += '#PJM -x PJM_LILO_GFSCACHE=/vol0004\n'
		calc_sh += '#PJM -S\n'
		calc_sh += 'export UDF_DEF_PATH="/vol0400/data/hp220245/octa/OCTA84/ENGINES/udf"\n'
		calc_sh += 'COGNAC="/vol0400/data/hp220245/octa/OCTA84/ENGINES/bin/unknown/cognac112"\n\n'
		calc_sh += '${COGNAC} -I ' + uin + ' -O' + uout + ' -n 48 \n'
		# バッチファイルを作成
		write_batchfile(var.calc_dir, f'deform.sh', calc_sh)
		#
		calc_all = "#!/bin/bash\n"
		calc_all += 'JID=`pjsub -z jid deform.sh`\n'
		calc_all += 'if [ $? -ne 0 ]; then\n'
		calc_all += 'exit 1\n'
		calc_all += 'fi\n'
		calc_all += 'set -- `pjwait $JID`\n'
		calc_all += 'if [ $2 != "0" -o $3 != "0" ]; then\n'
		calc_all += 'exit 1\n'
		calc_all += 'fi\n'
	udf_in =  os.path.join(var.calc_dir, uin)
	make_stepdeform_udf(udf_in)
	prev_udf = uin.replace("uin", "out")

	# 各放置時間における緩和計算を設定
	for i, condition in enumerate(var.step_relaxation):
		uin = f'relaxation_{i}_uin.udf'
		uout = uin.replace("uin", "out")
		if platform.system() == "Windows":
			make_title(var.title_name + '_' + base + f'_relaxation_{i}')
			var.batch += var.ver_Cognac + ' -I ' + uin + ' -O ' + uout + ' -n ' + str(var.core) +' \n'
		elif platform.system() == "Linux":
			calc_sh = '#PJM -L "node=1"\n'
			calc_sh += '#PJM -L "rscgrp=small"\n'
			calc_sh += '#PJM -L "elapse=72:00:00"\n'
			calc_sh += '#PJM -g hp220245\n'
			calc_sh += '#PJM -x PJM_LILO_GFSCACHE=/vol0004\n'
			calc_sh += '#PJM -S\n'
			calc_sh += 'export UDF_DEF_PATH="/vol0400/data/hp220245/octa/OCTA84/ENGINES/udf"\n'
			calc_sh += 'COGNAC="/vol0400/data/hp220245/octa/OCTA84/ENGINES/bin/unknown/cognac112"\n\n'
			calc_sh += '${COGNAC} -I ' + uin + ' -O' + uout + ' -n 48 \n'
			# バッチファイルを作成
			write_batchfile(var.calc_dir, f'relaxation_{i:}.sh', calc_sh)
			#
			calc_all += f'pjsub relaxation_{i:}.sh\n'
		udf_in =  os.path.join(var.calc_dir, uin)
		make_steprelax_udf(udf_in, prev_udf, condition)
	
	# 最長の緩和計算のUDFをリスタートにして長時間計算を繰り返す。
	repeat = var.step_repeat[0]
	for i in range(repeat):
		condition = var.step_repeat[1:]
		uin = f'repeat_{i}_uin.udf'
		udf_in =  os.path.join(var.calc_dir, uin)
		uout = uin.replace("uin", "out")
		if platform.system() == "Windows":
			make_title(var.title_name + '_' + base + f'_repeat_{i}')
			var.batch += var.ver_Cognac + ' -I ' + uin + ' -O ' + uout + ' -n ' + str(var.core) +' \n'
		elif platform.system() == "Linux":
			calc_sh = '#PJM -L "node=1"\n'
			calc_sh += '#PJM -L "rscgrp=small"\n'
			calc_sh += '#PJM -L "elapse=72:00:00"\n'
			calc_sh += '#PJM -g hp220245\n'
			calc_sh += '#PJM -x PJM_LILO_GFSCACHE=/vol0004\n'
			calc_sh += '#PJM -S\n'
			calc_sh += 'export UDF_DEF_PATH="/vol0400/data/hp220245/octa/OCTA84/ENGINES/udf"\n'
			calc_sh += 'COGNAC="/vol0400/data/hp220245/octa/OCTA84/ENGINES/bin/unknown/cognac112"\n\n'
			calc_sh += '${COGNAC} -I ' + uin + ' -O' + uout + ' -n 48 \n'
			# バッチファイルを作成
			write_batchfile(var.calc_dir, f'repeat_{i:}.sh', calc_sh)
			#
			calc_all += f'JID=`pjsub -z jid repeat_{i:}.sh`\n'
			calc_all += 'if [ $? -ne 0 ]; then\n'
			calc_all += 'exit 1\n'
			calc_all += 'fi\n'
			calc_all += 'set -- `pjwait $JID`\n'
			calc_all += 'if [ $2 != "0" -o $3 != "0" ]; then\n'
			calc_all += 'exit 1\n'
			calc_all += 'fi\n'
		make_steprelax_udf(udf_in, prev_udf, condition)
		prev_udf = uin.replace("uin", "out")
	#
	if platform.system() == "Windows":
		if var.step_deform == 'StepStretch':
			var.batch += f'evaluate_step_deform -f {var.func} -n {var.nu} -m stretch\n'
		elif var.step_deform == 'StepShear':
			var.batch += f'evaluate_step_deform -f {var.func} -n {var.nu} -m shear\n'
		# バッチファイルを作成
		write_batchfile(var.calc_dir, 'deform.bat', var.batch)
	elif platform.system() == "Linux":
		eval = "#!/bin/bash\n"
		if var.step_deform == 'StepStretch':
			eval += f'step_deform.py -f {var.func} -n {var.nu} -m stretch\n'
		elif var.step_deform == 'StepShear':
			eval += f'step_deform.py -f {var.func} -n {var.nu} -m shear\n'
		write_batchfile(var.calc_dir, 'eval.sh', eval)
		write_batchfile(var.calc_dir, 'calc_all.sh', calc_all)
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
		if var.step_deform_max < 1:
			u.put(-1*var.step_rate,	 					p + 'Cell_Deformation.Simple_Elongation.Initial_Strain_Rate.Rate')
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

#-----
def make_steprelax_udf(udf_in, prev_udf, condition):
	u = UDFManager(var.base_udf)
	# goto global data
	u.jump(-1)

	# Dynamics_Conditions
	p = 'Simulation_Conditions.Dynamics_Conditions.'
	u.put(100000.,		p + 'Max_Force')
	u.put(var.sim_time_div,	p + 'Time.delta_T')
	u.put(round(condition[0]/var.sim_time_div),	p + 'Time.Total_Steps')
	u.put(round(condition[0]/var.sim_time_div/condition[1]),	p + 'Time.Output_Interval_Steps')
	u.put(1.0,			p + 'Temperature.Temperature')
	u.put(0, 			p + 'Temperature.Interval_of_Scale_Temp')
	u.put(0,			p + 'Pressure_Stress.Pressure')

	# Output_Flags
	u.put([1, 1, 1], 'Simulation_Conditions.Output_Flags.Structure')
	
	# Read_Set_of_Molecules
	p = 'Initial_Structure.Read_Set_of_Molecules'
	u.put([prev_udf, -1], p)

	# Generate_Method
	p = 'Initial_Structure.Generate_Method.'
	u.put('Restart', 		p + 'Method')
	u.put([prev_udf, -1, 1, 1], 	p + 'Restart')

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
def write_batchfile(dir, filename, batch_file):
	# バッチファイルを作成
	f_batch = os.path.join(dir, filename)
	with open(f_batch, 'w') as f:
		f.write(batch_file)
	if platform.system() == "Linux":
		os.chmod(f_batch, 0o744)
	return

#######################################
# サブディレクトリを使うバッチファイルを作成
def make_batch_series(subdir_list, dir, task, filename, option):
	batch_series = ''
	for subdir in subdir_list:
		if platform.system() == "Windows":
			batch_series += 'cd /d %~dp0\\' + subdir +'\n'
			batch_series += task
			batch_series += 'cd /d %~dp0\n'
		elif platform.system() == "Linux":
			batch_series += 'cd ./' + subdir +'\n'
			batch_series += task
			batch_series += 'cd ../\n'
	if option != '':
		batch_series += option
	write_batchfile(dir, filename, batch_series)
	return

##########################
# Main
if __name__=='__main__':
	deform()