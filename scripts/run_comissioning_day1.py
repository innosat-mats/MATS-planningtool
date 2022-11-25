from mats_planningtool import configFile as configFile
from mats_planningtool.XMLGenerator.XML_gen import XML_filter


#3040 STAR

configfile = configFile.configFile("data/comissioning/configfile_3040_STAR.json")
configfile.output_dir = "data/comissioning/"
configfile.CheckConfigFile()

#configfile.Timeline_gen()

configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3040_22112222112201STAR.json")


# # 3050 Limb-functional

# configfile = configFile.configFile("data/comissioning/configfile_3050_LMBF.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# #configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3050_22112222112001LMBF.json")


# #3051 Limb-functional

# configfile = configFile.configFile("data/comissioning/configfile_3051_LMBF.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# #configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3051_22112222112001LMBF.json")

# #3101 Operational mode V1

# configfile = configFile.configFile("data/comissioning/configfile_3101_MODE5.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# #configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3101_22112222112001MODE5.json")
