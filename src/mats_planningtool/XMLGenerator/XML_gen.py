# -*- coding: utf-8 -*-
"""This module contains the core function of the *XML_gen* program and the first subfunction of *XML_gen*.

In this module is the base of the XML-tree defined and initial values such as the 
start and end time and also duration of the timeline are calculated. Goes through the 
supplied *Science Mode Timeline* List chronologically and calls for the corresponding function in one of the modules located in the *Modes_and_Tests* subpackage. \n

Any settings given in the *Science Mode Timeline* file will overide the use of the same settings stated in the set *Configuration File*.

All CMDs are stated in the "InnoSat Payload Timeline XML Defintion" document. 

*XML_gen* goes through the *Science Mode Timeline* chronologically and calls for functions from the modules inside the *Modes_and_Tests* package.

These functions then uses the settings given in the *Science Mode Timeline* or in the set *Configuration File* to calculate parameters to be used by their CMDs.

Then they either call directly for a Command function, located in the *Commands* module, inside the *Macros_Commands* package, or call for a Macro function located in the *Macros* module, inside the *Macros_Commands* package.

A Macro is a combination of commonly used CMDs. For more information see the *Macros* module inside the *Macros_Commands* package.

**Adding your own Mode:** \n

To add your own Mode to be converted into CMDs using *XML_gen* you need to follow these steps: \n

 - Go into the *Modes* module, inside the *Modes_and_Tests* package. At the bottom you should find a Mode template function called "XML_generator_X". Copy this function. Replace the X for the name of your Mode.
 - Calculate or define any appropriate parameters for your Mode's CMDs/Macros.
 - Now use these parameters to add any calls for Macros/Command functions located in the modules inside the *Macros_Commands* package. By default there is a call for the *TC_acfLimbPointingAltitudeOffset* CMD and the *Operational_Limb_Pointing_macro* as an example. You can remove these and add any combination of CMDs and macros as you like. 
 - It is recommended (but not necessary) to also give the new Mode its own "Configuration function" inside the *_ConfigFile*. This function will hold tuneable settings for the Mode, such as pointing altitude for the *TC_acfLimbPointingAltitudeOffset* CMD.

You should now have a working Mode in XML_gen. Feel free to check the other Modes defined in the *MODES* module to understand how they are implemented. There are also some outcommented lines of code which you might find useful when defining your Mode. 
These outcommented rows of code calls for Mode and CCD settings from the *Configuration File*, and by using *dict_comparator* it compares those Mode settings to the Mode settings given in the *Science Mode Timeline*. Lastly there is a outcommented call for a Macro called *Operational_Limb_Pointing_macro*.

**Note:** Keep in my that the duration of the Mode is scheduled in OPT.Timeline_gen and is given in the generated Science Mode Timeline. When adding CMDs and Macros to a new Mode, make sure that there is enough time scheduled for them.

"""

from .Modes_and_Tests import MODES, Tests, SeparateCMDsAndProcedures
from lxml import etree
import ephem
import logging
import sys
import time
import os
import json
import importlib
import datetime

from mats_planningtool import Library
#from mats_planningtool_Config_File import Timeline_settings, initialConditions, Logger_name, Version

Logger = logging.getLogger("OPT_logger")


def XML_generator(configFile, SCIMOD_Path):
    """The core function of the XML_gen program.

    Reads a *Science Mode Timeline* .json file. Then chronologically goes though the *Science Mode Timeline*, calling for the *XML_generator_select* function.
    Any settings stated in the *Science Mode Timeline* will override any similar ones given in the set *Configuration File*.
    Also calls for XML_Initial_Basis_Creator to setup a XML tree which will be used to write CMDs to.

    Arguments:
        SCIMOD_Path (str): A string containing the path to the Science Mode Timeline .json file.
    Returns:
        None

    """

    ######## Try to Create a directory for storage of output files #######
    try:
        os.mkdir(configFile.output_dir)
    except:
        pass

    "Reset temporary Globals"
    configFile.latestRelativeTime = 0
    configFile.current_pointing = None
    configFile.LargestSetTEXPMS = 0

    ############# Set up Logger #################################
    Library.SetupLogger(configFile.Logger_name())

    Logger.info('Start of Program')
    Logger.info('')

    ################# Read Science Mode Timeline json file ############
    with open(SCIMOD_Path, "r") as read_file:
        SCIMOD = json.load(read_file)
    ################# Read Science Mode Timeline json file ############

    Logger.info('Science Mode Timeline Used: '+SCIMOD_Path)

    "Check if there are Timeline_settings given in the Science Mode Timeline"
    if(str(SCIMOD[0][0]) == 'Timeline_settings'):
        Timeline_settings_from_Timeline = SCIMOD[0][5]
        Timeline_settings = Library.dict_comparator(
            Timeline_settings_from_Timeline, configFile.Timeline_settings())
        version = SCIMOD[0][4][-2:]
        Logger.info('Timeline_settings found in Science Mode Timeline. Using them')

        TLE_from_Timeline = SCIMOD[0][4]

    else:
        raise ValueError(
            'Timeline_settings not found in Science Mode Timeline. Using the ones in the chosen ConfigFile')

    #"Save the Timeline_settings to be used in a Global variable"
    #Globals.Timeline_settings = Timeline_settings

    ################ Get settings for Timeline from Config module ############
    timeline_duration = Timeline_settings['duration']['duration']
    Logger.info('timeline_duration: '+str(timeline_duration))

    timeline_start = ephem.Date(Timeline_settings['start_date'])
    Logger.info('timeline_start: '+str(timeline_start))

    ########    Call function to create XML-tree basis ##########################
    Logger.info('Call function XML_Initial_Basis_Creator')
    Logger.info('')
    root = XML_Initial_Basis_Creator(
        timeline_start, timeline_duration, SCIMOD_Path, configFile,version)

    ######## Loop through SCIMOD TIMELINE lIST, selecting one mode at a time #####
    Logger.info('Loop through Science Mode Timeline List')

    for x in range(len(SCIMOD)):

        Entry_Name = str(SCIMOD[x][0])
        StartDate = str(SCIMOD[x][1])
        EndDate = str(SCIMOD[x][2])
        Settings = SCIMOD[x][3]

        Logger.info('')
        Logger.info('Iteration number: '+str(x+1))
        Logger.info(Entry_Name)

        "Skip the first entry if it only contains Timeline_settings"
        if(str(SCIMOD[x][0]) == 'Timeline_settings'):
            continue

        Logger.debug('Start Date: '+StartDate)
        Logger.debug('End Date: '+EndDate)

        mode_duration = round((ephem.Date(EndDate) - ephem.Date(StartDate)) * 24*3600)
        relativeTime = round((ephem.Date(StartDate)-ephem.Date(timeline_start))*24*3600)
        Logger.debug('mode_duration: '+str(mode_duration))
        Logger.debug('relativeTime: '+str(relativeTime))

        if(relativeTime >= timeline_duration):
            Logger.warning('relativeTime is exceeding timeline_duration!!!')
            raise ValueError

        if(ephem.Date(StartDate) < timeline_start or mode_duration+relativeTime > timeline_duration):
            Logger.warning(
                Entry_Name+', is not scheduled within the boundaries of the timeline!!!')
            raise ValueError

        Logger.debug('Call XML_generator_select')
        XML_generator_select(root=root, duration=mode_duration, relativeTime=relativeTime,
                             name=Entry_Name, date=ephem.Date(StartDate), Settings=Settings, Timeline_settings=Timeline_settings, configFile=configFile)

    ### Rewrite path string to allow it to be in the name of the generated XML command file ###
    SCIMOD_Path = SCIMOD_Path.replace('\\', '_')
    SCIMOD_Path = SCIMOD_Path.replace('/', '_')
    SCIMOD_Path = SCIMOD_Path.replace('.json', '')

    ### Write finished XML-tree with all commands to a file #######

    XML_TIMELINE = get_timeline_name(configFile,Timeline_settings) 
        
    Logger.info('Write XML-tree to: '+XML_TIMELINE)
    f = open(XML_TIMELINE, 'w')
    f.write(etree.tostring(root, pretty_print=True, encoding='unicode'))
    f.close()

    statinfo = os.stat(XML_TIMELINE)
    SizeOfXML = statinfo.st_size
    DataLimitInBytes = 20*10**6
    if(SizeOfXML > DataLimitInBytes):
        input('Size of XML Timeline file exceeds allowed datalimit (20Mb). Press enter to acknowledge')

    "Reset temporary Globals"
    configFile.latestRelativeTime = 0
    configFile.current_pointing = None
    configFile.LargestSetTEXPMS = 0
    logging.shutdown()

    return XML_TIMELINE


################### XML-tree basis creator ####################################

def XML_Initial_Basis_Creator(timeline_start, timeline_duration, SCIMOD_Path, configFile,version):
    '''Subfunction, Construct Basis of XML document and adds the description container.

    Arguments: 
        timeline_start (ephem.Date): Starting date of the Timeline. On the form of the ephem.Date class.
        timeline_duration (int): Duration of the timeline [s].
        SCIMOD_Path (str): The path as a string to the Science Mode Timeline .json file used in this run.

    Returns:
        (lxml.etree.Element): The basis of the XML tree created with lxml.

    '''

    TimelineStart_Tuple = timeline_start.tuple()

    Timeline_settings = configFile.Timeline_settings()
    "Because of rounding errors in ephem.Date 0 seconds might be 59.9999... causing error. Add half a second here to fix this error."
    if(int(round(TimelineStart_Tuple[5])) == 60):
        TimelineStart_Tuple = ephem.Date(timeline_start + ephem.second/2).tuple()

    TimelineStart_datetime = datetime.datetime(TimelineStart_Tuple[0], TimelineStart_Tuple[1], TimelineStart_Tuple[2],
                                               TimelineStart_Tuple[3], TimelineStart_Tuple[4], int(round(TimelineStart_Tuple[5])))

    StartingDate = TimelineStart_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    
    StartingDate_name = TimelineStart_datetime.strftime("%Y%m%d")
    Generationdate_name = datetime.datetime.now().strftime("%Y%m%d")
    #earliestStartingDate = ephem.Date(timeline_start).datetime().strftime("%Y-%m-%dT%H:%M:%S")
    #latestStartingDate = ephem.Date(timeline_start).datetime().strftime("%Y-%m-%dT%H:%M:%S")

    root = etree.Element('InnoSatTimeline', originator='OHB', sdbVersion='9.5.99.2')

    root.append(etree.Element('description'))

    ID = configFile.ID()
    Name = configFile.Name()

    etree.SubElement(root[0], 'timelineID', procedureIdentifier='STP-MTS-' + ID,
                     descriptiveName=StartingDate_name+Generationdate_name+version+Name, version=version)

    etree.SubElement(root[0], 'changeLog')
    etree.SubElement(root[0][1], 'changeLogItem', version=version,
                     date=str(datetime.date.today()), author=configFile.Author())
    root[0][1][0].text = "The file was created using OPT"

    etree.SubElement(root[0], 'validity')
    etree.SubElement(root[0][2], 'startingDate')
    root[0][2][0].text = StartingDate
    etree.SubElement(root[0][2], 'scenarioDuration')
    root[0][2][1].text = str(timeline_duration)

    etree.SubElement(root[0], 'comment')
    root[0][3].text = "This command sequence is an Innosat timeline for MATS created with OPT. Science Mode Timeline used to generate: " + \
        SCIMOD_Path+', Configuration File used: '+configFile.config_file_name

    root.append(etree.Element('listOfCommands'))

    return root

####################### End of XML-tree basis creator #############################


####################### Mode selecter ###################################

def XML_generator_select(name, root, date, duration, relativeTime, Settings, Timeline_settings, configFile):
    '''Subfunction, Selects corresponding mode, test or CMD function in the package *Modes_and_Tests* from the variable *name*.

    Calls for any function named *X* in the modules *MODES*, *SeparateCmds*, and *Tests*, where X is the string in the input *name*.

    Arguments: 
        name (str): The name of the of the mode or test as a string. The name in the XML_generator_name function in OPT_XML_generator_MODES
        root (lxml.etree.Element): XML tree structure. Main container object for the ElementTree API.
        date (ephem.Date): Starting date of the Mode. On the form of the ephem.Date class.
        duration (int): The duration of the mode [s] as an integer class.
        relativeTime (int): The starting time of the mode with regard to the start of the timeline [s] as an integer class
        Settings (dict): Dictionary containing the settings of the Mode, CMD, or Test given in the Science_Mode_Timeline. 
        Timeline_settings (dict): Dictionary containing the settings of the Timeline given in the *Science_Mode_Timeline*. If no Timeline settings were present in the Science Mode Timeline, they were instead taken from the *Configuration File*.

    Returns:
        None
    '''

    try:
        Mode_Test_SeparateCmd_func = getattr(MODES, name)
    except AttributeError:
        try:
            Mode_Test_SeparateCmd_func = getattr(Tests, name)
        except AttributeError:
            try:
                Mode_Test_SeparateCmd_func = getattr(SeparateCMDsAndProcedures, name)
            except AttributeError:
                Logger.error('No XML-generator is defined for '+name)
                raise AttributeError

    "Check if any settings were given in the Science Mode Timeline"
    if(len(Settings.keys()) == 0):
        Mode_Test_SeparateCmd_func(
            root, date, duration, relativeTime, Timeline_settings, configFile)
    else:
        Mode_Test_SeparateCmd_func(root, date, duration, relativeTime,
                                   Timeline_settings, configFile, Settings)


####################### End of Mode selecter #############################

####################### XML-splitter #####################################

def XML_splitter(XML_TIMELINE,splitdates):
    '''Tool to split XMLtimelines into several shorter timelines

    The tool splits a timesline at a list of given times. The splitter ensures that the splitting do not occur
    in the middle of a mode (for calibration modes) or in the middle of a macro (for operational modes). 

    Arguments: 
        XML_TIMELINE (str): Filename of timeline to split in chronological order
        splitdates (list): list of datetime objects where the splitting shall be done
        
    Returns:
        None
    '''

    tree = etree.parse(XML_TIMELINE)
    root = tree.getroot()
    startdate = datetime.datetime.strptime(root[0][2][0].text,'%Y-%m-%dT%H:%M:%S')

    if splitdates[0]<startdate:
        raise ValueError('splitting cannot occur prior to first command')

    time_of_last_command = startdate
    splittime_index = 0

    for command in root[1]:
        time_of_command = startdate + datetime.timedelta(seconds=int(root[1][command][0].text))
        if time_of_last_command < splitdates[splittime_index] < time_of_command:
            pass

        


def XML_filter(XML_TIMELINE,commandstr):
    '''Tool to remove a specific procedure from an XML timeline

    Arguments: 
        XML_TIMELINE (str): Filename of timeline to split in chronological order
        command (str): procedure/command to remove
        
    Returns:
        None
    '''

    tree = etree.parse(XML_TIMELINE)
    root = tree.getroot()

    f = open(XML_TIMELINE[:-4]+'_non_filtered.xml', 'w')
    f.write(etree.tostring(root, pretty_print=True, encoding='unicode'))
    f.close()

    for command in root[1].findall('command'):
        if command.attrib['mnemonic']==commandstr:
            Logger.info('Removing ' + commandstr + ': from ' + XML_TIMELINE)
            root[1].remove(command)
    
    Logger.info('Write XML-tree to: '+XML_TIMELINE)
    f = open(XML_TIMELINE, 'w')
    f.write(etree.tostring(root, pretty_print=True, encoding='unicode'))
    f.close()
    return


def get_timeline_name(configFile,Timeline_settings):

    XML_TIMELINE = os.path.join(configFile.output_dir, 'STP-MTS-' + configFile.ID() + '_' + 
            datetime.datetime.strptime(Timeline_settings['start_date'],'%Y/%m/%d %H:%M:%S').strftime('%y%m%d') +
            datetime.datetime.now().strftime('%y%m%d') + configFile.Version() + configFile.Name() +'.xml')

    return XML_TIMELINE