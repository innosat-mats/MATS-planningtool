from mats_planningtool import configFile as configFile
from mats_planningtool.XMLGenerator.XML_gen import XML_filter

#3040 Star

configfile = configFile.configFile("data/comissioning/configfile_3040_STAR.json")
configfile.output_dir = "data/comissioning/"
configfile.CheckConfigFile()

configfile.Timeline_gen()
# configfile.XML_gen()