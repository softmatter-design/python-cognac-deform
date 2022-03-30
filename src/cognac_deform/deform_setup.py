#!/usr/bin/env python
# -*- coding: utf-8 -*-
################################################################
# from statistics import mode
import cognac_deform
################################################################

##### Set Target #####
# 使用するCognacのバージョンを入れてください。
Ver_Cognac = "cognac112"
# ネットワーク条件のファイル名
f_data = "calc.dat"
# シミュレーションに使用するコア数
core = 6

def_mode = 'shear'

if def_mode == 'elong':
	# 応力評価スクリプト名
	stress_eval = "read_stress.py"
	# 計算で使用するディレクトリ
	calc_dir = "Elong_calc"
	##### Conditions #####
	# これらは変形レートのリストであり、rate=lambda/tau
	rate_list = [1e-2, 1e-3, 5e-4] # 
	# シミュレーションの時間分割
	time_div = 0.01
	# 伸長伸度
	deform_max = 4
	# これは１ステップ計算での伸長度　Res = lambda/1_step
	res = 0.02
elif def_mode == 'shear':
	# 応力評価スクリプト名
	stress_eval = "read_stress.py"
	# 計算で使用するディレクトリ
	calc_dir = "Shear_calc"
	# これらは変形レートのリスト
	rate_list = [2e-3, 1e-3, 5e-4, 2e-4, 1e-4] # 
	# シミュレーションの時間分割
	time_div = 0.01
	# 伸長伸度
	deform_max = 4
	res = 0.02
##### Main #####
def main():
	setup = cognac_deform.DeformSetup(Ver_Cognac, calc_dir, f_data, core, stress_eval, rate_list, time_div, deform_max, res, def_mode)
	setup.make_all()
	return
################################################################################
#      Main     #
################################################################################
if __name__=='__main__':
	main()
