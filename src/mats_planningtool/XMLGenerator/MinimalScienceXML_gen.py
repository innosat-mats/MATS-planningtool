# -*- coding: utf-8 -*-
"""Contains the core function of the *MinimalScienceXMLGenerator*, 
which creates a minimal Science XML file with fixed Commands with arguments taken from the chosen *Configuration File*.

The minimal Science XML file defines the procedure for OHB to upload to the satellite after unscheduled payload shutdown.
"""
from .Modes_and_Tests.Macros_Commands import Macros, Commands
from lxml import etree
import logging
import os
import importlib
import datetime

from mats_planningtool import Globals, Library

OPT_Config_File = importlib.import_module(Globals.Config_File)
# from mats_planningtool_Config_File import Timeline_settings, initialConditions, Logger_name, Version

Logger = logging.getLogger(OPT_Config_File.Logger_name())


def MinimalScienceXMLGenerator():
    """The Core function of *MinimalScienceXML_gen* part of *OPT*.

    The generated XML will: \n
        1. Run TC_pafCCDBIAS
        2. Run TC_pafCCDFlushBadColumns
        3. Run TC_pafCCDBadColumn
        4. Run Operational_Limb_Pointing_macro with CCD_macro equal to 'HighResIR'.

    The time between CMDs (CMD_separation) is fixed to 2 s. The start date is not set and needs to be added manually later.

    """

    "######## Try to Create a directory for storage of output files #######"
    try:
        os.mkdir("Output")
    except:
        pass

    "Reset temporary Globals"
    Globals.latestRelativeTime = 0
    Globals.current_pointing = None
    Globals.LargestSetTEXPMS = 0

    "############# Set up Logger #################################"
    Library.SetupLogger(OPT_Config_File.Logger_name())

    "############# Get Settings from the Configuration File #########"
    CCDBIAS_settings = OPT_Config_File.CCDBIAS_settings()
    CCDFlushBadColumns_settings = OPT_Config_File.CCDFlushBadColumns_settings()
    CCDBadColumn_settings = OPT_Config_File.CCDBadColumn_settings()
    Timeline_settings = OPT_Config_File.Timeline_settings()
    CCD_settings = OPT_Config_File.CCD_macro_settings("HighResIR")
    PM_settings = OPT_Config_File.PM_settings()

    "######## SET CMD separation to 2 sec #################"
    Timeline_settings["CMD_separation"] = 2

    "################### XML-tree basis creator ####################################"

    root = etree.Element("InnoSatTimeline", originator="OHB", sdbVersion="9.5.99.2")

    root.append(etree.Element("description"))

    etree.SubElement(
        root[0],
        "timelineID",
        procedureIdentifier="",
        descriptiveName="MinimalScience",
        version="1.0",
    )

    etree.SubElement(root[0], "changeLog")
    etree.SubElement(
        root[0][1],
        "changeLogItem",
        version="1.0",
        date=str(datetime.date.today()),
        author="David Skanberg",
    )
    root[0][1][0].text = "The file was created using OPT"

    etree.SubElement(root[0], "validity")
    etree.SubElement(root[0][2], "startingDate")
    root[0][2][0].text = ""
    etree.SubElement(root[0][2], "scenarioDuration")
    root[0][2][1].text = ""

    etree.SubElement(root[0], "comment")
    root[0][3].text = (
        "This command sequence is a 'Minimum Science' Innosat timeline for MATS, created with OPT. Configuration File used: "
        + Globals.Config_File
    )

    root.append(etree.Element("listOfCommands"))

    "####################### End of XML-tree basis creator #############################"

    "####################### Minimum Science CMDs ######################################"

    relativeTime = Commands.TC_pafCCDBIAS(
        root,
        relativeTime=1,
        CCDSEL=CCDBIAS_settings["CCDSEL"],
        VGATE=CCDBIAS_settings["VGATE"],
        VSUBST=CCDBIAS_settings["VSUBST"],
        VRD=CCDBIAS_settings["VRD"],
        VOD=CCDBIAS_settings["VOD"],
        Timeline_settings=Timeline_settings,
    )

    relativeTime = Commands.TC_pafCCDFlushBadColumns(
        root,
        relativeTime,
        CCDSEL=CCDFlushBadColumns_settings["CCDSEL"],
        Timeline_settings=Timeline_settings,
    )

    relativeTime = Commands.TC_pafCCDBadColumn(
        root,
        relativeTime,
        CCDSEL=CCDBadColumn_settings["CCDSEL"],
        NBC=CCDBadColumn_settings["NBC"],
        BC=CCDBadColumn_settings["BC"],
        Timeline_settings=Timeline_settings,
    )

    relativeTime = Macros.Operational_Limb_Pointing_macro(
        root,
        relativeTime,
        CCD_settings,
        PM_settings,
        pointing_altitude=Timeline_settings["StandardPointingAltitude"],
        Timeline_settings=Timeline_settings,
    )

    "Update duration in the Timeline"
    root[0][2][1].text = str(relativeTime + Timeline_settings["mode_separation"])

    "####################### End of Minimum Science CMDs ################################"

    "### Write finished XML-tree with all commands to a file #######"
    XML_TIMELINE = os.path.join("Output", "XML_TIMELINE__MinimalScience_.xml")
    Logger.info("Write XML-tree to: " + XML_TIMELINE)
    f = open(XML_TIMELINE, "w")
    f.write(etree.tostring(root, pretty_print=True, encoding="unicode"))
    f.close()

    "Reset temporary Globals"
    Globals.latestRelativeTime = 0
    Globals.current_pointing = None
    Globals.LargestSetTEXPMS = 0

    logging.shutdown()
