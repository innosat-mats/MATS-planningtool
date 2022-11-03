#3000 FFEXP
from mats_planningtool import configFile as configFile

configfile = configFile.configFile("data/early_harvest/configfile_3000_FFEXP.json")
configfile.output_dir = "data/early_harvest/"
configfile.CheckConfigFile()

#configfile.Timeline_gen(test=True)

# #Manually remove sciencemode and set dates for snapshots in timeline_file
configfile.XML_gen("data/early_harvest/Science_Mode_Timeline_3000_22110922110301TFFEXP.json")


#3010 WDWJQ
from mats_planningtool import configFile as configFile

configfile = configFile.configFile("data/early_harvest/configfile_3010_WDWJQ.json")
configfile.output_dir = "data/early_harvest/"
configfile.CheckConfigFile()

#configfile.Timeline_gen(test=True)

# #Manually remove sciencemode and set dates for snapshots in timeline_file
configfile.XML_gen("data/early_harvest/Science_Mode_Timeline_3010_22110922110301TWDWJQ.json")

# #3020 FFDAR
from mats_planningtool import configFile as configFile

configfile = configFile.configFile("data/early_harvest/configfile_3020_FFDAR.json")
configfile.output_dir = "data/early_harvest/"
configfile.CheckConfigFile()

#configfile.Timeline_gen(test=True)

#Manually remove sciencemode and set dates for snapshots in timeline_file
configfile.XML_gen("data/early_harvest/Science_Mode_Timeline_3020_22110922110301TFFDAR.json")


#3030 OP3S
from mats_planningtool import configFile as configFile

configfile = configFile.configFile("data/early_harvest/configfile_3030_OP5.json")
configfile.output_dir = "data/early_harvest/"
configfile.CheckConfigFile()

#configfile.Timeline_gen(test=True)

#Manually remove sciencemode and set dates for snapshots in timeline_file
#configfile.XML_gen("data/early_harvest/Science_Mode_Timeline_3030_22110922110301TOP5.json",test=True)

