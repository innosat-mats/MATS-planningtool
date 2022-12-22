from mats_planningtool import configFile as configFile
from mats_planningtool.XMLGenerator.XML_gen import XML_filter


# configfile = configFile.configFile("data/comissioning/configfile_3105_MODE1y.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()    
    
# configfile.Timeline_gen()
# configfile.XML_gen()

configfile = configFile.configFile("data/comissioning/configfile_3106_MODE1y.json")
configfile.output_dir = "data/comissioning/"
configfile.CheckConfigFile()    
    
configfile.Timeline_gen()
configfile.XML_gen()

# configfile = configFile.configFile("data/comissioning/configfile_3160_ODIN4.json")
# configfile.output_dir = "data/comissioning/"
# configfile.CheckConfigFile()    
    
# configfile.Timeline_gen()
# configfile.XML_gen()