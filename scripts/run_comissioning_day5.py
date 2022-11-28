from mats_planningtool import configFile as configFile
from mats_planningtool.XMLGenerator.XML_gen import XML_filter

# 3053 Limb-functional

# configfile = configFile.configFile("data/comissioning/configfile_3180_SIMRAC.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# #configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3180_22112822112501SIMRAC.json")


# # 3053 Limb-functional

# configfile = configFile.configFile("data/comissioning/configfile_3181_SIMR2C.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# #configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3181_22112822112501SIMR2C.json")

# # 3080 Rayleigh step

# configfile = configFile.configFile("data/comissioning/configfile_3080_RAY60.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# #configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3080_22112222112501RAY60.json")


configfile = configFile.configFile("data/comissioning/configfile_3080_RAY120.json")
configfile.output_dir = "data/comissioning/"
configfile.CheckConfigFile()

#configfile.Timeline_gen()

configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3080_22112222112501RAY120.json")