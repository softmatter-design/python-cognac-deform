# Values used for calculation
deform_udf = ''
# 使用するCognacのバージョン
ver_Cognac = "cognac112"
# シミュレーションに使用するコア数
core = 1

read_udf = ''
base_udf = ''

system_size = 0.
sim_time_div = 0.01

##### Conditions #####
# 変形モード
simple_def_mode = ''
sim_deform = ''
sim_rate_list = []
sim_rate = ''
sim_deform_max = 1
sim_resolution = 0.
sim_basedir = ''
sim_ratedir = ''
sim_dirlist = []

# Cyclic deformation
cyclic_deform = ''
cyc_deform_cond_dic = {}
# cyc_repeat = []
# cyc_ratelist = []
# cyc_resolution = []

cyc_dir = ''
cyc_readudf = ''
cyc_direction = ''
cyc_rotate = []
cyc_dirlist = []

cyc_rate = 0
cyc_count = 0
cyc_resol = 0

# Step deformation
step_deform = ''
step_deform_max = 0.
step_rate = 0.
step_steps = 0
step_deform_time = []

step_dir = ''
step_relaxation = []
step_repeat = []

step_rotate = []
step_dirlist = []


# step_readudf = ''
# step_direction = ''


func = 4
nu = 0.1


# 計算で使用するディレクトリ
title_base = ''
title_name = ''
calc_dir = ""
batch = ''
batch2 = ''
# batch3 = ''