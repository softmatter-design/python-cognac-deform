# Values used for calculation

# 使用するCognacのバージョン
ver_Cognac = "cognac112"
# シミュレーションに使用するコア数
core = 1

read_udf = ''
base_udf = ""

##### Conditions #####
# 変形モード
def_mode = ''
# 変形レートのリスト
rate_list = [1e-2, 1e-3, 5e-4] # 
# 伸長伸度
deform_max = 4
# これは１ステップ計算での伸長度　Res = lambda/1_step
resolution = 0.02
#
time_div = 0.01

func = 4
nu = 0.1


# 応力評価スクリプト名
stress_eval = "read_stress.py"
# 計算で使用するディレクトリ
calc_dir = ""

batch = ''