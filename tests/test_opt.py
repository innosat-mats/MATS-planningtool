# -*- coding: utf-8 -*-
"""
Created on Mon Feb 4 16:56:23 2021

Main test script showcasing how to use the main parts of OPT.

@author: Ole Martin Christensen
"""

from mats_planningtool import configFile as configFile
from mats_planningtool import timeLine as timeLine

configfile = "./data/config_file_original.json"

configfile_original = configFile.configFile(configfile,
                                            "2020/9/25 16:45:00",
                                            TLE1="1 54321U 19100G   20172.75043981 0.00000000  00000-0  75180-4 0  0014",
                                            TLE2="2 54321  97.7044   6.9210 0014595 313.2372  91.8750 14.93194142000010",
                                            )


# "Check the currently chosen Configuration File and the plausibility of its values. Prints out the currently used start date and TLE"
configfile_original.CheckConfigFile()

# "Create a Science Mode Timeline (.json file) depending on the settings in the Configuration File"
configfile_original.Timeline_gen()

# "Predict state and attitude data from the Science Mode Timeline and plot the results"
# Data_MATS, Data_LP, Time, Time_OHB = OPT.Timeline_Plotter(
#     "Output/Science_Mode_Timeline__OPT_Config_File.json", Timestep=20
# )

# "Convert the Science Mode Timeline into payload and platform CMDs as a .xml file)"

configfile_original.XML_gen()

# "Plot the example Science Mode Timeline together with the example h5 file and the example STK generated .csv file"
# Data_MATS, Data_LP, Timescience_mode_timeline_path, Time_OHB = OPT.Timeline_Plotter(
#     "OPT/Example_Science_Mode_Timeline__OPT_Config_File.json",
#     STK_CSV_PATH="OPT/ExampleCSVfile.csv",
#     OHB_H5_Path="OPT/ExampleH5file_LEVEL_1A_PLATF_20200120-094217_20200120-102136.hdf5",
#     Timestep=20,
# )

# "Open plots previously created with Timeline_Plotter"
# OPT.Plot_Timeline_Plotter_Plots(
#     "Output/Science_Mode_Timeline__OPT_Config_File/Timeline_Plotter_PlotsAndData"
# )

# # "Return the active science mode and its settings at a specfic date from a Science Mode Timeline"
# Mode, Parameters = OPT.Timeline_analyzer(
#     "Output/Science_Mode_Timeline__OPT_Config_File.json", "2020-06-20 19:30:00"
# )

# "Create a Minimal Science XML which is defined directly in the Source Code under _XMLGenerator.MinimalScienceXML_gen.py"
configfile_original.MinimalScienceXML_gen()

# "Schedule StartUpCMDs and all defined commisioning phase Tests with default settings"
configfile_original.XML_gen(
    "test_data/Example_Science_Mode_Timeline__Commisioning_Phase_Tests.json")

configfile_original.PLUTOGenerator(
    "Output/XML_TIMELINE__FROM__Output_Science_Mode_Timeline__config_file_original.xml",
    "Output/optest_pluto.plp",
)

configfile_original.PLUTOGenerator(
    "Output/XML_TIMELINE__MinimalScience_.xml", "Output/minimal_science_pluto.plp")
