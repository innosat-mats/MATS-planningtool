from mats_planningtool import configFile as configFile
from mats_planningtool.XMLGenerator.XML_gen import XML_filter

# #3120 CROP

# configfile = configFile.configFile("data/comissioning/configfile_3120_CROP.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# #configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3120_22120622120502CROP.json")

#3103 Operational mode 1 with JPEG compression

configfile = configFile.configFile("data/comissioning/configfile_3105_MODE1y.json")
configfile.output_dir = "data/comissioning/"
configfile.CheckConfigFile()

# configfile.Timeline_gen()
# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3105_22120622120502MODE1y.json")

configfile.Timeline_gen()
configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3105_22120722120501MODE1y.json")