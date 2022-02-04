# -*- coding: utf-8 -*-
"""
Created on Mon Feb 4 16:56:23 2021

Main test script showcasing how to use the main parts of OPT.

@author: Ole Martin Christensen
"""

from mats_planningtool import configFile as configFile
import filecmp
import pickle
from deepdiff import DeepDiff

############################
## CHECK CODE USING TEST CONFIG FILE
############################

configfile = "./test_data/config_file_test.json"

configfile_test = configFile.configFile(
    configfile,
    "2020/9/25 16:45:00",
    TLE1="1 54321U 19100G   20172.75043981 0.00000000  00000-0  75180-4 0  0014",
    TLE2="2 54321  97.7044   6.9210 0014595 313.2372  91.8750 14.93194142000010",
)

configfile_test.output_dir = 'test_data_output'

# Check the currently chosen Configuration File and the plausibility of its values. Prints out the currently used start date and TLE
configfile_test.CheckConfigFile()

# Create a Science Mode Timeline (.json file) depending on the settings in the Configuration File
configfile_test.Timeline_gen()
assert filecmp.cmp('test_data_output/Science_Mode_Timeline_config_file_test.json','test_data/output/Science_Mode_Timeline_config_file_test.json')


# Predict state and attitude dataconfig from the Science Mode Timeline and plot the results
Data_MATS, Data_LP, Time, Time_OHB = configfile_test.Timeline_Plotter(
    "test_data/output/Science_Mode_Timeline_config_file_test.json", Timestep=20
)

with open('test_data/output/timeline_plotter_output.pkl', 'rb') as f:
    timeline_plotter_data = pickle.load(f)
assert DeepDiff(timeline_plotter_data[0],Data_MATS) == {}
assert DeepDiff(timeline_plotter_data[1],Data_LP) == {}
assert DeepDiff(timeline_plotter_data[2],Time) == {}
assert DeepDiff(timeline_plotter_data[3],Time_OHB) == {}

# Convert the Science Mode Timeline into payload and platform CMDs as a .xml file)

configfile_test.XML_gen(SCIMOD_Path="test_data/output/Science_Mode_Timeline_config_file_test.json")
assert filecmp.cmp('test_data_output/XML_TIMELINE__FROM__test_data_output_Science_Mode_Timeline_config_file_test.xml','test_data/output/XML_TIMELINE__FROM__test_data_output_Science_Mode_Timeline_config_file_test.xml')

# Plot the example Science Mode Timeline together with the example h5 file and the example STK generated .csv file
Data_MATS, Data_LP, Timescience_mode_timeline_path, Time_OHB = configfile_test.Timeline_Plotter(
      "test_data/Example_Science_Mode_Timeline__OPT_Config_File.json",
      STK_CSV_PATH="test_data/ExampleCSVfile.csv",
      OHB_H5_Path="test_data/ExampleH5file_LEVEL_1A_PLATF_20200120-094217_20200120-102136.hdf5",
      Timestep=20,
      FractionOfDataUsed=0.1,
 )

with open('test_data/output/timeline_plotter_OHB_output.pkl', 'rb') as f:
    timeline_plotter_data = pickle.load(f)
assert DeepDiff(timeline_plotter_data[0],Data_MATS) == {}
assert DeepDiff(timeline_plotter_data[1],Data_LP) == {}
assert DeepDiff(timeline_plotter_data[2],Timescience_mode_timeline_path) == {}
assert DeepDiff(timeline_plotter_data[3],Time_OHB) == {}

# Open plots previously created with Timeline_Plotter
configfile_test.Plot_Timeline_Plotter_Plots(
    "Output/Science_Mode_Timeline__OPT_Config_File/Timeline_Plotter_PlotsAndData"
)

#Make pluto script
configfile_test.PLUTOGenerator(
     "test_data/XML_TIMELINE__FROM__test_data_output_Science_Mode_Timeline_config_file_test.xml",
     "test_data_output/optest_pluto.plp",
)
assert filecmp.cmp('test_data_output/optest_pluto.plp','test_data/output/optest_pluto.plp')

############################
## TEST ORIGINAL TIMELINE
############################

# Test original timeline
configfile = configFile.configFile("./test_data/config_file_original.json")
configfile.output_dir = 'test_data_output'
configfile.CheckConfigFile()
configfile.Timeline_gen()
assert filecmp.cmp('test_data_output/Science_Mode_Timeline_config_file_original.json','test_data/output/Science_Mode_Timeline_config_file_original.json')

# Return the active science mode and its settings at a specfic date from a Science Mode Timeline
Mode, Parameters = configfile.Timeline_analyzer(
    "test_data/output/Science_Mode_Timeline_config_file_original.json", "2020-06-20 19:30:00"
)

with open('test_data/output/timeline_analyzer_output.pkl', 'rb') as f:
    timeline_analyzer_output = pickle.load(f)
assert DeepDiff(timeline_analyzer_output[0],Mode) == {}
assert DeepDiff(timeline_analyzer_output[1],Parameters) == {}

# Create a Minimal Science XML which is defined directly in the Source Code under _XMLGenerator.MinimalScienceXML_gen.py
configfile.MinimalScienceXML_gen()
assert filecmp.cmp('test_data_output/XML_TIMELINE__MinimalScience_.xml','test_data/output/XML_TIMELINE__MinimalScience_.xml')

# Generate pluto script
configfile_test.PLUTOGenerator(
    "test_data/XML_TIMELINE__MinimalScience_.xml", "test_data_output/minimal_science_pluto.plp"
)
assert filecmp.cmp('test_data_output/minimal_science_pluto.plp','test_data/output/minimal_science_pluto.plp')

############################
## TEST WITH TIMELINE FROM OPERATIONAL MODE TEST (DATE ?)
############################

# Schedule StartUpCMDs and all defined commisioning phase Tests with default settings
configfile.XML_gen(
     "test_data/Example_Science_Mode_Timeline__Commisioning_Phase_Tests.json"
)
assert filecmp.cmp('test_data_output/XML_TIMELINE__FROM__test_data_Example_Science_Mode_Timeline__Commisioning_Phase_Tests.xml','test_data/output/XML_TIMELINE__FROM__test_data_Example_Science_Mode_Timeline__Commisioning_Phase_Tests.xml')
