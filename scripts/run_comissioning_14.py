from mats_planningtool import configFile as configFile
from mats_planningtool.XMLGenerator.XML_gen import XML_filter

#3040 Star

configfile = configFile.configFile("data/comissioning/configfile_3040_STAR.json")
configfile.output_dir = "data/comissioning/"
configfile.CheckConfigFile()

#configfile.Timeline_gen()
configfile.XML_gen()

# #3103 Operational mode 1 with JPEG compression and crop

# configfile = configFile.configFile("data/comissioning/configfile_3106_MODE1y.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# configfile.Timeline_gen()
# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3106_22120822120602MODE1y.json")