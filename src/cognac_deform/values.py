# Values used for calculation

# 使用するCognacのバージョン
Ver_Cognac = "cognac112"
# シミュレーションに使用するコア数
core = 6

# ネットワーク条件のファイル名
f_data = "calc.dat"

# 変形モード
def_mode = 'shear'
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