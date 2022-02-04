from mats_planningtool import configFile as configFile

configfile_original = configFile.configFile(
    "data/Optest-21-12-10/config_file_xml_test_opmode_only.json"
)
configfile_original.CheckConfigFile()
configfile_original.Timeline_gen()
configfile_original.XML_gen()
configfile_original.PLUTOGenerator(max_wait_time=60)
