from mats_planningtool import configFile as configFile
from mats_planningtool.XMLGenerator.XML_gen import XML_filter


# #3000 FFEXP

configfile = configFile.configFile("data/comissioning/configfile_3040_STAR.json")
configfile.output_dir = "data/comissioning/"
configfile.CheckConfigFile()

#configfile.Timeline_gen()

# # #Manually remove sciencemode and set dates for snapshots in timeline_file
configfile.XML_gen("data/comissioning/Science_Mode_Timeline_3040_22112222111701STAR.json")
#XML_filter("data/early_harvest/STP-MTS-3000_22110922110904FFEXP.xml", "TC_acfLimbPointingAltitudeOffset")
