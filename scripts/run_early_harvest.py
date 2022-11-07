from mats_planningtool import configFile as configFile
from mats_planningtool.XMLGenerator.XML_gen import XML_filter


# #3000 FFEXP

configfile = configFile.configFile("data/early_harvest/configfile_3000_FFEXP.json")
configfile.output_dir = "data/early_harvest/"
configfile.CheckConfigFile()

#configfile.Timeline_gen()

# # #Manually remove sciencemode and set dates for snapshots in timeline_file
configfile.XML_gen("data/early_harvest/Science_Mode_Timeline_3000_22110922110703FFEXP.json")
XML_filter("data/early_harvest/STP-MTS-3000_22110922110703FFEXP.xml", "TC_acfLimbPointingAltitudeOffset")

# # #3010 WDWJQ
from mats_planningtool import configFile as configFile

configfile = configFile.configFile("data/early_harvest/configfile_3010_WDWJQ.json")
configfile.output_dir = "data/early_harvest/"
configfile.CheckConfigFile()

# configfile.Timeline_gen()

# # #Manually remove sciencemode and set dates for snapshots in timeline_file
configfile.XML_gen("data/early_harvest/Science_Mode_Timeline_3010_22110922110703WDWJQ.json")
XML_filter("data/early_harvest/STP-MTS-3010_22110922110703WDWJQ.xml", "TC_acfLimbPointingAltitudeOffset")

# #3020 FFDAR
from mats_planningtool import configFile as configFile

configfile = configFile.configFile("data/early_harvest/configfile_3020_FFDAR.json")
configfile.output_dir = "data/early_harvest/"
configfile.CheckConfigFile()

# configfile.Timeline_gen()

#Manually remove sciencemode and set dates for snapshots in timeline_file
configfile.XML_gen("data/early_harvest/Science_Mode_Timeline_3020_22110922110703FFDAR.json")
XML_filter("data/early_harvest/STP-MTS-3020_22110922110703FFDAR.xml", "TC_acfLimbPointingAltitudeOffset")

# # #3030 OP3S
from mats_planningtool import configFile as configFile

configfile = configFile.configFile("data/early_harvest/configfile_3030_OP5.json")
configfile.output_dir = "data/early_harvest/"
configfile.CheckConfigFile()

# configfile.Timeline_gen()

# # #Manually remove sciencemode and set dates for snapshots in timeline_file
configfile.XML_gen("data/early_harvest/Science_Mode_Timeline_3030_22110922110703OP5.json")
XML_filter("data/early_harvest/STP-MTS-3030_22110922110703OP5.xml", "TC_acfLimbPointingAltitudeOffset")

#Add go to idle mode at the end

# #3030 OP6S
from mats_planningtool import configFile as configFile

configfile = configFile.configFile("data/early_harvest/configfile_3030_OP5T2.json")
configfile.output_dir = "data/early_harvest/"
configfile.CheckConfigFile()

# configfile.Timeline_gen()

configfile.XML_gen("data/early_harvest/Science_Mode_Timeline_3030_22110922110703OP5T2.json")
XML_filter("data/early_harvest/STP-MTS-3030_22110922110703OP5T2.xml", "TC_acfLimbPointingAltitudeOffset")

#Add go to idle mode at the end