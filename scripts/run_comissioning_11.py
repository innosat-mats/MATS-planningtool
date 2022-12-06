from mats_planningtool import configFile as configFile
from mats_planningtool.XMLGenerator.XML_gen import XML_filter
    
#3103 Operational mode 5 with binned calibration

# configfile = configFile.configFile("data/comissioning/configfile_3160_ODIN1.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3160_22120222120101ODIN1.json")

# configfile = configFile.configFile("data/comissioning/configfile_3161_ODIN2.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()

# configfile.Timeline_gen()

# configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3161_22120222120101ODIN2.json")

# #3103 Operational mode 5

configfile = configFile.configFile("data/comissioning/configfile_3104_MODE1y.json")
configfile.output_dir = "data/comissioning/"
configfile.CheckConfigFile()

configfile.Timeline_gen()

configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3104_22120422120101MODE1y.json")

# #3103 Operational mode 1

configfile = configFile.configFile("data/comissioning/configfile_3104_MODE5.json")
configfile.output_dir = "data/comissioning/"
configfile.CheckConfigFile()

configfile.Timeline_gen()

configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3104_22120322120101MODE5.json")

#3103 Operational mode 5 with JPEG compression

configfile = configFile.configFile("data/comissioning/configfile_3105_MODE1y.json")
configfile.output_dir = "data/comissioning/"
configfile.CheckConfigFile()

configfile.Timeline_gen()

configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3105_22120522120101MODE1y.json")
