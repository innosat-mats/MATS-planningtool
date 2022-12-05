from mats_planningtool import configFile as configFile
from mats_planningtool.XMLGenerator.XML_gen import XML_filter

#3103 Operational mode 120

configfile = configFile.configFile("data/comissioning/configfile_3040_STAR.json")
configfile.output_dir = "data/comissioning/"
configfile.CheckConfigFile()

#configfile.Timeline_gen()

configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3040_22120522120507STAR.json")

#3103 Operational mode 1 with JPEG compression

configfile = configFile.configFile("data/comissioning/configfile_3105_MODE1y.json")
configfile.output_dir = "data/comissioning/"
configfile.CheckConfigFile()

#configfile.Timeline_gen()
configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3105_22120622120501MODE1y.json")