# Values used for calculation

# 使用するCognacのバージョン
ver_Cognac = "cognac112"
# シミュレーションに使用するコア数
core = 1

read_udf = ''
base_udf = ''

system_size = 0.

##### Conditions #####
# 変形モード
simple_def_mode = ''
sim_deform = ''
sim_rate_list = []
sim_deform_max = 1
sim_resolution = 0.
sim_time_div = 0.01

# Cyclic deformation
cyclic_deform = ''
cyc_deform_max = []
cyc_repeat = []
cyc_ratelist = []
cyc_resolution = []

cyc_dir = ''
cyc_readudf = ''
cyc_direction = ''
cyc_dirlist = []

cyc_def_max = 0
cyc_rate = 0
cyc_count = 0
cyc_resol = 0

# Step deformation
step_deform = ''
step_deform_max = 0.
step_rate = 0.
step_time = 0
step_resolution = 0
step_time2 = 0
step_resolution2 = 0

step_dir = ''
step_readudf = ''
step_direction = ''
step_dirlist = []


func = 4
nu = 0.1


# 計算で使用するディレクトリ
calc_dir = ""
batch = ''