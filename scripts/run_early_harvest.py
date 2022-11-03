# #%%
# #3000 FFINT
# from mats_planningtool import configFile as configFile

# configfile = configFile.configFile("data/early_harvest/configfile_3000_FFINT.json")
# configfile.output_dir = "data/early_harvest/"
# configfile.CheckConfigFile()
# configfile.Timeline_gen()

# #Manually remove sciencemode and set dates for snapshots in timeline_file


# # %%
from mats_planningtool import configFile as configFile

configfile = configFile.configFile("data/early_harvest/configfile_3010_WDWJQ.json")
configfile.output_dir = "data/early_harvest/"
configfile.CheckConfigFile()
#configfile.Timeline_gen()
# %%

#Manually remove sciencemode and set dates for snapshots in timeline_file
configfile.XML_gen("data/early_harvest/Science_Mode_Timeline_3010_221109221103WDWJQ.json")


# %%
