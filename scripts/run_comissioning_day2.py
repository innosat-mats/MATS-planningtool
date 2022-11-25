from mats_planningtool import configFile as configFile
from mats_planningtool.XMLGenerator.XML_gen import XML_filter



# #3060 Nadir-functional

# configfile = configFile.configFile("data/comissioning/configfile_3060_NADF.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# #configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3060_22112322112202NADF.json")



# #3040 STAR

# configfile = configFile.configFile("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/comissioning/configfile_3040_STAR.json")
# configfile.output_dir = "/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/comissioning/"
# configfile.CheckConfigFile()

# #configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3040_22112322112303STAR.json")


# # 3052 Limb-functional

# configfile = configFile.configFile("data/comissioning/configfile_3052_LMBF.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# #configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3052_22112322112202LMBF.json")


# 3053 Limb-functional

# configfile = configFile.configFile("data/comissioning/configfile_3053_LMBF.json")
# configfile.output_dir = "data/comissioning/"
#configfile.CheckConfigFile()

#configfile.Timeline_gen()

#configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3053_22112322112303LMBF.json")

#3101 Operational mode V1

configfile = configFile.configFile("data/comissioning/configfile_3102_MODE5.json")
configfile.output_dir = "data/comissioning/"
configfile.CheckConfigFile()

#configfile.Timeline_gen()

configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3102_22112322112302MODE5.json")
