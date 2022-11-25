from mats_planningtool import configFile as configFile
from mats_planningtool.XMLGenerator.XML_gen import XML_filter




# #3041 STAR

# configfile = configFile.configFile("data/comissioning/configfile_3040_STAR.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# configfile.Timeline_gen()

# #configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3041_22112322112101STAR.json")


# # 3052 Limb-functional

# configfile = configFile.configFile("data/comissioning/configfile_3052_LMBF.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# #configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3052_22112322112202LMBF.json")


# # 3053 Limb-functional

# configfile = configFile.configFile("data/comissioning/configfile_3053_LMBF.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# configfile.Timeline_gen()

#configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3053_22112322112101LMBF.json")

#3101 Operational mode V1

configfile = configFile.configFile("data/comissioning/configfile_3170_PHOTO.json")
configfile.output_dir = "data/comissioning/"
configfile.CheckConfigFile()

#configfile.Timeline_gen()

configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3170_22112522112501PHOTO.json")
