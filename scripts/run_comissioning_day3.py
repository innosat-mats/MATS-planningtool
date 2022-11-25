from mats_planningtool import configFile as configFile
from mats_planningtool.XMLGenerator.XML_gen import XML_filter


# #3060 Nadir-functional

# configfile = configFile.configFile("data/comissioning/configfile_3060_NADF.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# #configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3060_22112422112302NADF.json")



# #3041 STAR

# configfile = configFile.configFile("data/comissioning/configfile_3041_STAR.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# configfile.Timeline_gen()

#configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3041_22112322112101STAR.json")


# # 3054 Limb-functional

# configfile = configFile.configFile("data/comissioning/configfile_3054_LMBF.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# #configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3054_22112422112302LMBF.json")


# # 3055 Limb-functional

# configfile = configFile.configFile("data/comissioning/configfile_3055_LMBF.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# #configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3055_22112422112302LMBF.json")

#3101 Operational mode V1

configfile = configFile.configFile("data/comissioning/configfile_3102_MODE5.json")
configfile.output_dir = "data/comissioning/"
configfile.CheckConfigFile()

configfile.Timeline_gen()

configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3103_22112422112403MODE5.json")
