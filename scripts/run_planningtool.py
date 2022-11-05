from mats_planningtool import configFile as configFile


def get_test_configfile():

    configfile = "./data/config_file_opmode.json"

    configfile_test = configFile.configFile(
        configfile,
        "2022/11/04 18:00:00",
        TLE1="1 99988U 22123    22304.76424065  .00004664  00000-0  44774-3 0 00000",
        TLE2="2 99988 097.6561 307.5659 0012827 298.3476 106.0390 14.93086308000015",
    )

    configfile_test.output_dir = 'test_data_output'

    return configfile_test

configfile_test = get_test_configfile()

# Convert the Science Mode Timeline into payload and platform CMDs as a .xml file)

configfile_test.XML_gen(SCIMOD_Path="test_data/output/Science_Mode_Timeline_config_file_test_short.json")
# configfile_original.PLUTOGenerator(max_wait_time=60)
