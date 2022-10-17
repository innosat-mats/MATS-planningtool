from mats_planningtool import configFile as configFile

configfile_original = configFile.configFile(
    "data/orbitsim-22-10-17/config_file_orbitsim.json"
    )
configfile_original.CheckConfigFile()
configfile_original.Timeline_gen()
configfile_original.XML_gen()
# configfile_original.PLUTOGenerator(max_wait_time=60)
