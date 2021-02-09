from mats_planningtool import Library

import json


class timeLine:

    Library.SetupLogger('timeline')

    def __init__(self, timeline_file_name):

        self.timeline_file_name = timeline_file_name

        with open(self.timeline_file_name) as json_file:
            OPT_Timeline = json.load(json_file)

        self.OPT_Timeline = OPT_Timeline
        self.current_pointing = None

        "Reset temporary Globals"
        self.latestRelativeTime = 0
        self.current_pointing = None
        self.LargestSetTEXPMS = 0

    def Version(self):
        return "0.1"

    def Logger_name(self):
        return "timeLine"

    def Timeline_settings(self):
        """Returns settings related to a *Science Mode Timeline* as a whole.

        **Keys:**
            'start_date': Sets the starting date of the timeline (str), (example: '2018/9/3 08:00:40'). Contains _Globals.StartTime if *Set_ConfigFile* has been ran with a start date as an input. Otherwise any value stated here.  \n
            'duration': Sets the duration [s] of the timeline. Will drastically change the runtime of *Timeline_gen*. A runtime of around 15 min is estimated for a duration of 1 week (int) \n

            'Mode1_2_5_minDuration': Minimum amount of available time needed, inbetween scheduled Modes/CMDs in a *Science Mode Timeline*, to allow the scheduling of *Operational Science Modes* when running *Timeline_gen* [s]. \n
            'mode_separation': Time in seconds for an added buffer when determining the duration of a Mode/CMD. (int) \n
            'CMD_duration': Sets the amount of time scheduled for separate PayloadCMDs when using *Timeline_gen*. Should be large enough to allow any separate CMD to finish processing.  (int) \n

            'yaw_correction': Determines if yaw correction shall be used for the duration of the timeline. Mainly impacts simulations of MATS's pointing. But also determines the argument of the ArgEnableYawComp CMD. (bool) \n
            'yaw_amplitude': Amplitude of the yaw function, A*cos(argument_of_latitude - B - phase), where B is angle between optical axis and negative velocity vector in the orbital plane. (float) \n
            'yaw_phase': Phase of the yaw function, A*cos(argument_of_latitude - B - phase), where B is angle between optical axis and negative velocity vector in the orbital plane. (float) \n
            'Choose_Operational_Science_Mode': Set to 1, 2, or 5 to choose either Mode1, Mode2, or Mode5 as the *Operational Science Mode*. Set to 0 to schedule either Mode1 or Mode2 depending of the time of the year.
            'StandardPointingAltitude': Sets pointing altitude in meters for the timeline. Used to set the pointing altitude of *Operational Science Modes* and to calculate the duration of attitude freezes (because attitude freezes last until the pointing altitude is reorientated to this value).  (int) \n

            'CMD_separation': Changes the separation in time [s] between commands that are scheduled in *XML_gen*. If set too large, it is possible that not enough time is scheduled for the duration of Modes, causing Modes to overlap in time. Impacts the estimated duration of certain Science Modes in *Timeline_gen*. (float) \n
            'pointing_stabilization': The maximum time it takes for an attitude change to stabilize [s]. Used before scheduling certain CMDs in *XML_gen* to make sure that the attitude has been stabilized after running *TC_acfLimbPointingAltitudeOffset*. Impacts the estimated duration of Science Modes in *Timeline_gen*. (int) \n
            'CCDSYNC_ExtraOffset': Extra offset time [ms] that is added to an estimated ReadoutTime when calculating TEXPIOFS for the CCD Synchronize CMD. (int) \n
            'CCDSYNC_ExtraIntervalTime': Extra time [ms] that is added to the calculated Exposure Interval Time (for example when calculating arguments for the CCD Synchronize CMD or nadir TEXPIMS). (int) \n
            'CCDSYNC_Waittime': Time to wait after running CCDSYNC to allow for the synchronization to be set correctly (should be longer than longest TEXPIMS) 

        Returns:
            (:obj:`dict`): Timeline_settings
        """

        return self.OPT_Timeline[0][3]

    def XML_gen(self):
        """Invokes the XML generator program part of Operational Planning Tool for MATS.

        Converts a *Science Mode Timeline*  (.json file) containing a list of scheduled Science Modes/CMDs/Tests into Payload and Platform commands and saves them as a .xml command file.  \n
        Settings for the operation of the program are stated in the chosen *Configuration File*, set by *Set_ConfigFile*.
        Settings given in the *Science Mode Timeline* override the settings given in the chosen *Configuration file* or set with *Set_ConfigFile*.

        Arguments: 
            science_mode_timeline_path (str): Path to the .json file containing the Science Mode Timeline.

        Returns: 
            None
        """

        from .XMLGenerator.XML_gen import XML_generator

        "Initialize current_pointing to None"
        self.current_pointing = None

        XML_generator(self.timeline_file_name, self)

    def MinimalScienceXML_gen(self):
        """Invokes the *MinimalScienceXML_gen* part of the *OPT*.

        Creates an .xml file with fixed CMDs which purpose is to define a flight procedure which is ran on the satellite 
        following unscheduled power termination of the payload.
        Runs startup CMDs and sets the payload in operation mode with the CCD macro *HighResIR*.
        The CMD staggering is fixed. No date is given in the generated XML and will need to be added manually.
        Uses settings for the CMDs from the currently set *Configuration File*.

        """

        from mats_planningtool.XMLGenerator.MinimalScienceXML_gen import MinimalScienceXMLGenerator

        MinimalScienceXMLGenerator(self)
