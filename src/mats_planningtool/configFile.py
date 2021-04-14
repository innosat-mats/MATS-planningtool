from mats_planningtool import Library

import json
import os


class configFile:

    Library.SetupLogger("configFile")

    def __init__(
        self,
        config_file_name,
        date="2020/6/20 18:32:42",
        TLE1="1 54321U 19100G   20172.75043981 0.00000000  00000-0  75180-4 0  0014",
        TLE2="2 54321  97.7044   6.9210 0014595 313.2372  91.8750 14.93194142000010",
    ):

        self.config_file_name = config_file_name
        self.TLE1 = TLE1
        self.TLE2 = TLE2
        self.date = date

        with open(self.config_file_name) as json_file:
            OPT_Config_File = json.load(json_file)

        self.OPT_Config_File = OPT_Config_File

        self.OPT_Config_File["Timeline_settings"]["duration"]["duration"] = (
            self.OPT_Config_File["Timeline_settings"]["duration"]["day"] * 24 * 3600
            + self.OPT_Config_File["Timeline_settings"]["duration"]["hours"] * 3600
            + self.OPT_Config_File["Timeline_settings"]["duration"]["seconds"]
        )

        self.OPT_Config_File["Mode120_settings"]["TimeToConsider"]["TimeToConsider"] = (
            self.OPT_Config_File["Mode120_settings"]["TimeToConsider"]["hours"] * 3600
            + self.OPT_Config_File["Mode120_settings"]["TimeToConsider"]["seconds"]
        )

        self.OPT_Config_File["Mode120_settings"]["TimeSkip"]["TimeSkip"] = (
            self.OPT_Config_File["Mode120_settings"]["TimeSkip"]["hours"] * 3600
            + self.OPT_Config_File["Mode120_settings"]["TimeSkip"]["seconds"]
        )

        self.OPT_Config_File["Mode121_122_123_settings"]["TimeToConsider"][
            "TimeToConsider"
        ] = (
            self.OPT_Config_File["Mode121_122_123_settings"]["TimeToConsider"]["hours"]
            * 3600
            + self.OPT_Config_File["Mode121_122_123_settings"]["TimeToConsider"][
                "seconds"
            ]
        )

        self.OPT_Config_File["Mode121_122_123_settings"]["TimeSkip"]["TimeSkip"] = (
            self.OPT_Config_File["Mode121_122_123_settings"]["TimeSkip"]["hours"] * 3600
            + self.OPT_Config_File["Mode121_122_123_settings"]["TimeSkip"]["seconds"]
        )

        self.OPT_Config_File["Mode124_settings"]["TimeToConsider"]["TimeToConsider"] = (
            self.OPT_Config_File["Mode124_settings"]["TimeToConsider"]["hours"] * 3600
            + self.OPT_Config_File["Mode124_settings"]["TimeToConsider"]["seconds"]
        )

        self.current_pointing = None
        self.latestRelativeTime = 0
        self.LargestSetTEXPMS = 0
        self.Mode120Iteration = 1
        self.Mode124Iteration = 1

    def Logger_name(self):
        """Returns the name of the shared logger.

        Returns:
            (str): Logger_name

        """

        return self.OPT_Config_File["Logger_name"]

    def Version(self):
        """'Returns the version ID of this Configuration File.

        The version ID should only be changed when the default *Configuration File*, _ConfigFile in OPT, is changed.

        Returns:
            (str): version_name

        """

        return self.OPT_Config_File["version_ID"]

    def Scheduling_priority(self):
        """Returns the Modes (except *Operational Science Modes* (Mode 1,2,5)) and StartUpCMDs planned to be schedueled in a *Science Mode Timeline* using *Timeline_gen*.

        **Available choices are:** \n

            - 'ArgEnableYawComp',
            - 'Payload_Power_Toggle',
            - 'TurnONCCDs',
            - 'CCDFlushBadColumns',
            - 'CCDBadColumn',
            - 'PM',
            - 'HTR',
            - 'CCDBIAS',
            - 'Mode100',
            - 'Mode110',
            - 'Mode120',
            - 'Mode121',
            - 'Mode122',
            - 'Mode123',
            - 'Mode124',
            - 'Mode131',
            - 'Mode132',
            - 'Mode133',
            - 'Mode130',
            - 'Mode134'

        The order of which the Modes/StartUpCMDs appear is also their priority order (top-down). \n
        Repeat Modes/CMDs to schedule them several times, though there is currently not feature that allows multiple Modes/CMDs
        to be scheduled with different settings. Some settings that does not affect the duration of the Mode can still be changed manually afterwards in the generated Science Mode Timeline.
        Each string must be equal to the name of a function imported in the *_Timeline_generator.Modes.Modes_Header* module. \n

        'Payload_Power_Toggle', 'TurnONCCDs', 'ArgEnableYawComp', 'CCDFlushBadColumns', 'CCDBadColumn', 'PM', 'CCDBIAS' are called StartUpCMDs and are recommended to run at the start of each
        timeline, as they together reset and initialize the intrument. If "HTR" is scheduled, arguments is needed to be entered manually into the created *Science Mode Timeline* because of safety reasons. \n

        'Payload_Power_Toggle' is a OHB procedure that safely power toggles the instrument. \n

        'TurnONCCDs' is a special CCD macro that turns on the CCDs.

        Returns:
            (:obj:`list` of :obj:`str`): Modes_priority

        """

        return self.OPT_Config_File["Modes_priority"]

    def getTLE(self):
        """Returns the TLE as two strings in a list.

        Returns a TLE from the *Globals* module if *Set_ConfigFile* has been ran with a TLE as input.
        Otherwise returns any TLE values stated here.

        Returns:
            (:obj:`list` of :obj:`str`): First Element is the first TLE row, and the second Element is the second row.

        """

        if (not self.TLE1 == ("")) and (not self.TLE2 == ("")):
            TLE1 = self.OPT_Config_File["TLE1"]
            TLE2 = self.OPT_Config_File["TLE2"]
        else:
            "If no TLE has been chosen with *Set_ConfigFile*, these values are used instead."
            TLE1 = (
                "1 54321U 19100G   20172.75043981 0.00000000  00000-0  75180-4 0  0014"
            )
            TLE2 = (
                "2 54321  97.7044   6.9210 0014595 313.2372  91.8750 14.93194142000010"
            )

        return [TLE1, TLE2]

    def Timeline_settings(self):
        """Returns settings related to a *Science Mode Timeline* as a whole.

        **Keys:**
            'start_date': Sets the starting date of the timeline (str), (example: '2018/9/3 08:00:40'). Contains Globals.StartTime if *Set_ConfigFile* has been ran with a start date as an input. Otherwise any value stated here.  \n
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

        Returns:
            (:obj:`dict`): Timeline_settings
        """
        return self.OPT_Config_File["Timeline_settings"]

    def Operational_Science_Mode_settings(self):
        """Returns settings related to Operational Science Modes (Mode1, 2, and 5).

        **Keys:**
            'lat': Applies only to Mode1! Sets in degrees the latitude (+ and -) that the LP crosses that causes the UV exposure to swith on/off. (int) \n
            'log_timestep': Used only in *XML_gen*. Sets the frequency of data being logged [s] for Mode1-2. Only determines how much of simulated data is logged for debugging purposes. (int) \n
            'timestep': Sets the timestep [s] of the XML generator simulation of Mode1-2. Will impact accuracy of command generation but also drastically changes the runtime of XML-gen. (int) \n
            'Choose_Mode5CCDMacro': Applies only to Mode5! Sets the CCD macro to be used by Mode5. Used as input to *CCD_macro_settings* in the ConfigFile (str).

        Returns:
            (:obj:`dict`): settings

        """

        return self.OPT_Config_File["Operational_Science_Mode_settings"]

    """
    def Mode5_settings():
        '''Returns settings related to Mode5.

        **Keys in returned dict:**
            'pointing_altitude': Sets in meters the altitude of the pointing command. If set to 0, Timeline_settings['StandardPointingAltitude'] will be used (int)

        Returns:
            (:obj:`dict`): settings

        '''

        settings = {'pointing_altitude': 110000}

        return settings

    """

    def Mode100_settings(self):
        """Returns settings related to Mode100.

        **Keys in returned dict:**
            'pointing_altitude_from': Sets in meters the starting altitude. Part in determining the estimated duration of the mode. (int) \n
            'pointing_altitude_to': Sets in meters the ending altitude. Part in determining the estimated duration of the mode. (int) \n
            'pointing_altitude_interval': Sets in meters the interval size of each succesive pointing. Part in determining the estimated duration of the mode. (int) \n
            'pointing_duration': Sets the time [s] from attitude stabilization until next pointing command. Part in determining the estimated duration of the mode. (int) \n
            'Exp_Time_IR': Sets starting exposure time [ms] as a integer. \n
            'Exp_Time_UV': Sets starting exposure time [ms] as a integer. \n
            'ExpTime_step': Sets in ms the interval size of both ExpTimeUV and ExpTimeIR for each succesive pointing. (int) \n
            'start_date': Sets the scheduled date for the mode as a str, (example: '2018/9/3 08:00:40'). If the date is set to '0', Timeline_settings['start_date'] will be used.

        Returns:
            (:obj:`dict`): settings

        """

        return self.OPT_Config_File["Mode100_settings"]

    def Mode110_settings(self):
        """Returns settings related to Mode110.

        **Keys in returned dict:**
            'pointing_altitude_from': Sets in meters the starting altitude of the sweep. Part in determining the estimated duration of the mode. (int) \n
            'pointing_altitude_to': Sets in meters the ending altitude of the sweep. Part in determining the estimated duration of the mode. (int) \n
            'sweep_rate': Sets the rate of the sweep in m/s. Part in determining the estimated duration of the mode. (int) \n
            'start_date': Sets the scheduled date for the mode as a str, (example: '2018/9/3 08:00:40'). If the date is set to '0', Timeline_settings['start_date'] will be used.
            'Exp_Time_IR': Sets exposure time [ms] of the IR CCDs. (int) \n
            'Exp_Time_UV': Sets exposure time [ms] of the UV CCDs. (int) \n

        Returns:
            (:obj:`dict`): settings

        """

        return self.OPT_Config_File["Mode110_settings"]

    def Mode120_settings(self):
        """Returns settings related to Mode120.

        **Keys in returned dict:**
            'pointing_altitude': Sets in meters the altitude of the pointing command. (int) \n
            'V_offset': Used only in *Timeline_gen*. Sets the Vertical-offset angle (position in FOV) in degrees for the star to have passed, when the attitude freeze command is scheduled.
            Multiple values can be set but additional values will only be used when Mode120 is scheduled several times. (list of int) \n
            'H_offset': Used only in *Timeline_gen*. Sets the maximum Horizontal-offset angle in degrees that determines if stars are visible. (int) \n
            'Vmag': Used only in *Timeline_gen*. Sets the Johnson V magnitude of stars to be considered (as a string expression, example '<2'). Drastically changes the runtime. \n
            'TimeToConsider': Used only in *Timeline_gen*. Sets the time in seconds for which scheduling is considered. Used to plan star calibration at the start of each timeline (useful as TLE accuracy deteriorates). Drastically affects simulation time. (int) \n
            'timestep': Used only in *Timeline_gen*. Sets timestep used in scheduling simulation [s]. Will impact scheduling accuracy. (int) \n
            'TimeSkip': Used only in *Timeline_gen*. Set the amount of seconds to skip ahead after one complete orbit is simulated. Will drastically change the runtime of the simulation. (int) \n
            'log_timestep': Used only in *Timeline_gen*. Sets the timestep of data being logged [s]. Only determines how much of simulated data is logged for debugging purposes.. (int) \n
            'automatic': Used only in *Timeline_gen*. Sets if 'start_date' will be calculated or user provided. True for calculated and False for user provided. (bool) \n
            'start_date':  Note! only applies if *automatic* is set to False. Used only in *Timeline_gen*. Sets the scheduled date for the mode as a str, (example: '2018/9/3 08:00:40'). If set to '0', Timeline_settings['start_date'] will be used. \n
            'freeze_start': Sets in seconds the time from start of the Mode to when the attitude freezes. Part in determining the estimated duration of the mode. (int) \n
            'freeze_duration': Sets in seconds the duration of the attitude freeze. Part in determining the estimated duration of the mode. If set to 0, it will be estimated to a
            value corresponding to the attitude being frozen until realigned with *Timeline_settings['StandardPointingAltitude']* (Normally around 50 s). (int) \n
            'SnapshotTime': Sets in seconds the time, from the start of the attitude freeze, to when the first Snapshot is taken. (int) \n
            'SnapshotSpacing': Sets in seconds the time inbetween Snapshots with individual CCDs. (int) \n
            'CCDSELs': List of CCDSEL arguments (except nadir) for which to take snapshots with. (list of int)

        Returns:
            (:obj:`dict`): settings

        """
        if self.OPT_Config_File["Mode120_settings"]["freeze_duration"] == 0:
            self.OPT_Config_File["Mode120_settings"][
                "freeze_duration"
            ] = Library.FreezeDuration_calculator(
                self.OPT_Config_File["Timeline_settings"]["StandardPointingAltitude"],
                self.OPT_Config_File["Mode120_settings"]["pointing_altitude"],
                self.getTLE()[1],
            )

        return self.OPT_Config_File["Mode120_settings"]

    def Mode121_122_123_settings(self):
        """Returns settings shared between Mode121-123.

        **Keys in returned dict:**
            'pointing_altitude': Sets in meters the altitude of the pointing command. (int) \n
            'H_FOV': Used only in *Timeline_gen*. Sets full Horizontal FOV of the Limb instrument in degrees. Used to determine if stars are visible. (float) \n
            'V_FOV': Used only in *Timeline_gen*. Sets full Vertical FOV of the Limb instrument in degrees. Used to determine if stars are visible. (float) \n
            'TimeToConsider': Used only in *Timeline_gen*. Sets the time in seconds for which scheduling is considered. Used to plan calibration at the start of each timeline (useful as TLE accuracy deteriorates). Drastically affects simulation time at the cost of fewer time slots being considered. (int) \n
            'Vmag': Used only in *Timeline_gen*. Sets the Johnson V magnitude of stars to be considered (as a string expression, example '<2'). Drastically changes the runtime. \n
            'timestep': Used only in *Timeline_gen*. Set timestep used in scheduling simulation [s]. Will impact scheduling accuracy. (int) \n
            'TimeSkip': Used only in *Timeline_gen*. Set the amount of seconds to skip ahead after one complete orbit is simulated. Will drastically change the runtime of the simulation. (float) \n
            'log_timestep': Used only in *Timeline_gen*. Sets the timestep of data being logged [s]. Only determines how much of simulated data is logged for debugging purposes. (int) \n
            'freeze_start': Sets in seconds, the time from start of the Mode to when the attitude freezes. Part in determining the estimated duration of the mode. (int) \n
            'freeze_duration': Sets in seconds the duration of the attitude freeze. Part in determining the estimated duration of the mode. If set to 0, it will be estimated to a
            value corresponding to the attitude being frozen until realigned with *Timeline_settings['StandardPointingAltitude']* (Normally around 50 s). (int) \n
            'SnapshotTime': Sets in seconds the time, from the start of the attitude freeze, to when the first Snapshot is taken. (int) \n
            'SnapshotSpacing': Sets in seconds the time inbetween Snapshots with individual CCDs. Needs to be larger than any CCD ReadoutTimes to avoid streaks. (int)

        Returns:
            (:obj:`dict`): settings

        """

        if self.OPT_Config_File["Mode121_122_123_settings"]["freeze_duration"] == 0:
            self.OPT_Config_File["Mode121_122_123_settings"][
                "freeze_duration"
            ] = Library.FreezeDuration_calculator(
                self.OPT_Config_File["Timeline_settings"]["StandardPointingAltitude"],
                self.OPT_Config_File["Mode121_122_123_settings"]["pointing_altitude"],
                self.getTLE()[1],
            )

        return self.OPT_Config_File["Mode121_122_123_settings"]

    def Mode121_settings(self):
        """Returns settings related to Mode121.

        **Keys in returned dict:**
            'start_date':  Note! only applies if *automatic* is set to False. Used only in *Timeline_gen*. Sets the scheduled date for the mode as a str, (example: '2018/9/3 08:00:40'). If set to '0', Timeline_settings['start_date'] will be used. \n
            'automatic': Used only in *Timeline_gen*. Sets if 'start_date' will be calculated or user provided. True for calculated and False for user provided. (bool) \n
            'CCDSELs': List of CCDSEL arguments (except nadir) for which to take snapshots with. (list of int)

        Returns:
            (:obj:`dict`): settings
        """

        Settings = self.OPT_Config_File["Mode121_settings"]
        CommonSettings = self.Mode121_122_123_settings()

        settings = {**CommonSettings, **Settings}

        return settings

    def Mode122_settings(self):
        """Returns settings related to Mode122.

        **Keys in returned dict:**
            'start_date':  Note! only applies if *automatic* is set to False. Used only in *Timeline_gen*. Sets the scheduled date for the mode as a str, (example: '2018/9/3 08:00:40'). If set to '0', Timeline_settings['start_date'] will be used. \n
            'automatic': Used only in *Timeline_gen*. Sets if 'start_date' will be calculated or user provided. True for calculated and False for user provided. (bool) \n
            'Exp_Time_IR': Sets exposure time [ms] of the IR CCDs. (int) \n
            'Exp_Time_UV': Sets exposure time [ms] of the UV CCDs. (int) \n

        Returns:
            (:obj:`dict`): settings
        """

        Settings = self.OPT_Config_File["Mode122_settings"]
        CommonSettings = self.Mode121_122_123_settings()

        settings = {**CommonSettings, **Settings}

        return settings

    def Mode123_settings(self):
        """Returns settings related to Mode123.

        **Keys in returned dict:**
            'start_date':  Note! only applies if *automatic* is set to False. Used only in *Timeline_gen*. Sets the scheduled date for the mode as a str, (example: '2018/9/3 08:00:40'). If set to '0', Timeline_settings['start_date'] will be used. \n
            'automatic': Used only in *Timeline_gen*. Sets if 'start_date' will be calculated or user provided. True for calculated and False for user provided. (bool) \n
            'Exp_Time_IR': Sets exposure time [ms] of the IR CCDs. (int) \n
            'Exp_Time_UV': Sets exposure time [ms] of the UV CCDs. (int) \n

        Returns:
            (:obj:`dict`): settings
        """

        Settings = self.OPT_Config_File["Mode123_settings"]
        CommonSettings = self.Mode121_122_123_settings()

        settings = {**CommonSettings, **Settings}

        return settings

    def Mode124_settings(self):
        """Returns settings related to Mode124.

        **Keys in returned dict:**
            'pointing_altitude': Sets in meters the altitude of the pointing command. (int) \n
            'V_offset': Used only in *Timeline_gen*. Sets the Vertical-offset angle (position in FOV) in degrees for the Moon to pass, for when the attitude freeze command is scheduled.
            Multiple values can be set but additional values will only be used when Mode124 is scheduled several times. (list of int) \n
            'H_offset': Used only in *Timeline_gen*. Sets the maximum H-offset angle from the optical axis in degrees that determines if the Moon is available. (float) \n
            'TimeToConsider': Used only in *Timeline_gen*. Sets the time in seconds for which scheduling is considered. Used to plan calibration at the start of each timeline (useful as TLE accuracy deteriorates). Drastically affects simulation time at the cost of fewer time slots being considered. (int) \n
            'timestep':  Used only in *Timeline_gen*. Sets in seconds the timestep during scheduling simulation [s]. Will impact scheduling accuracy. (int) \n
            'log_timestep': Used only in *Timeline_gen*. Sets the timestep of data being logged [s]. Only determines how much of simulated data is logged for debugging purposes. (int) \n
            'automatic':  Used only in *Timeline_gen*. Sets if the mode date is to be calculated or user provided. True for calculated or False for user provided. (bool) \n
            'start_date':  Note! only applies if *automatic* is set to False. Used only in *Timeline_gen*. Sets the scheduled date for the mode as a str, (example: '2018/9/3 08:00:40'). If set to '0', Timeline_settings['start_date'] will be used. \n
            'freeze_start': Sets in seconds the time from start of the Mode to when the attitude freeze command is scheduled. Part in determining the estimated duration of the mode. (int) \n
            'freeze_duration': Sets in seconds the duration of the attitude freeze. Part in determining the estimated duration of the mode. If set to 0, it will be estimated to a
            value corresponding to the attitude being frozen until realigned with *Timeline_settings['StandardPointingAltitude']*. (int) \n
            'SnapshotTime': Sets in seconds the time, from the start of the attitude freeze, to when the first Snapshot is taken. (int) \n
            'SnapshotSpacing': Sets in seconds the time inbetween Snapshots with individual CCDs. Needs to be larger than any CCD ReadoutTimes to avoid streaks. (int) \n
            'CCDSELs': List of CCDSEL arguments (except nadir) for which to take snapshots with. (list of int)

        Returns:
            (:obj:`dict`): settings

        """
        if self.OPT_Config_File["Mode124_settings"]["freeze_duration"] == 0:
            self.OPT_Config_File["Mode124_settings"][
                "freeze_duration"
            ] = Library.FreezeDuration_calculator(
                self.OPT_Config_File["Timeline_settings"]["StandardPointingAltitude"],
                self.OPT_Config_File["Mode124_settings"]["pointing_altitude"],
                self.getTLE()[1],
            )

        return self.OPT_Config_File["Mode124_settings"]

    def Mode130_settings(self):
        """Returns settings related to Mode130.

        **Keys in returned dict:**
            'pointing_altitude': Sets in meters the altitude of the pointing command. (int) \n
            'SnapshotSpacing': Sets in seconds the time inbetween Snapshots with individual CCDs. Part in determining the estimated duration of the mode. (int) \n
            'start_date': Sets the scheduled date for the mode as a str, (example: '2018/9/3 08:00:40'). If the date is set to '0', Timeline_settings['start_date'] will be used.

        Returns:
            (:obj:`dict`): settings

        """

        return self.OPT_Config_File["Mode130_settings"]

    def Mode131_settings(self):
        """Returns settings related to Mode131.

        **Keys in returned dict:**
            'pointing_altitude': Sets in meters the altitude of the pointing command. (int) \n
            'mode_duration': Sets the scheduled duration of the Mode in seconds. Must be long enough to allow any pointing stabilization, CCD synchronization (takes 1 TEXPIMS cycle to execute), and execution of CMDs to occur. (int) \n
            'start_date': Sets the scheduled date for the mode as a str, (example: '2018/9/3 08:00:40'). If the date is set to '0', Timeline_settings['start_date'] will be used.

        Returns:
            (:obj:`dict`): settings

        """

        return self.OPT_Config_File["Mode131_settings"]

    def Mode132_settings(self):
        """Returns settings related to Mode132.

        **Keys in returned dict:**
            'pointing_altitude': Sets in meters the altitude of the pointing command. (int) \n
            'start_date': Sets the scheduled date for the mode as a str, (example: '2018/9/3 08:00:40'). If the date is set to '0', Timeline_settings['start_date'] will be used. \n
            'Exp_Times_IR': Sets exposure times [ms] as a list of integers. Part in determining the estimated duration of the mode. Shall have equal length to 'Exp_Times_UV'.  \n
            'Exp_Times_UV': Sets exposure times [ms] as a list of integers. Part in determining the estimated duration of the mode. Shall have equal length to 'Exp_Times_IR'. \n
            'session_duration': Sets the duration [s] of each session spent in operational mode using the different exposure times in *Exp_Times*. Part in determining the estimated duration of the mode. (int)

        Returns:
            (:obj:`dict`): settings

        """

        return self.OPT_Config_File["Mode132_settings"]

    def Mode133_settings(self):
        """Returns settings related to Mode133.

        **Keys in returned dict:**
            'pointing_altitude': Sets in meters the altitude of the pointing command. (int) \n
            'start_date': Sets the scheduled date for the mode as a str, (example: '2018/9/3 08:00:40'). If the date is set to '0', Timeline_settings['start_date'] will be used. \n
            'Exp_Times_IR': Sets exposure times [ms] as a list of integers. Part in determining the estimated duration of the mode. Shall have equal length to 'Exp_Times_UV'.  \n
            'Exp_Times_UV': Sets exposure times [ms] as a list of integers. Part in determining the estimated duration of the mode. Shall have equal length to 'Exp_Times_IR'. \n
            'session_duration': Sets the duration [s] of each session spent in operational mode using the different exposure times in *Exp_Times_UV* and *Exp_Times_IR*. Part in determining the estimated duration of the mode. (int)

        Returns:
            (:obj:`dict`): settings

        """

        return self.OPT_Config_File["Mode133_settings"]

    def Mode134_settings(self):
        """Returns settings related to Mode134.

        **Keys in returned dict:**
            'pointing_altitude': Sets in meters the altitude of the pointing command. (int) \n
            'mode_duration': Sets the scheduled duration of the Mode in seconds. Must be long enough to allow any pointing stabilization, CCD synchronization (takes 1 TEXPIMS cycle to execute), and execution of CMDs to occur. (int) \n
            'start_date': Sets the scheduled date for the mode as a str, (example: '2018/9/3 08:00:40'). If the date is set to '0', Timeline_settings['start_date'] will be used.

        Returns:
            (:obj:`dict`): settings

        """

        return self.OPT_Config_File["Mode134_settings"]

    """
    def Mode201_settings():
        '''Returns settings related to Mode201.

        **Keys in returned dict:**
            'pointing_altitude': Sets in meters the altitude of the pointing command. \n
            'mode_duration': Sets the scheduled duration of the Mode in seconds. \n
            'start_date': Sets the scheduled date for the mode as a str, (example: '2018/9/3 08:00:40'). If the date is set to '0', Timeline_settings['start_date'] will be used.

        Returns:
            (:obj:`dict`): settings

        '''
        settings = {'pointing_altitude': 70000, 'mode_duration': 600, 'start_date': '0'}
        return settings



    def Mode203_settings():
        '''Returns settings related to Mode203.

        **Keys in returned dict:**
            'pitch': Sets the pitch axis maneuver.

        Returns:
            settings (:obj:`dict`)

        '''
        settings = {'pitch': 180}
        return settings
    """

    def PWRTOGGLE_settings(self):
        """Returns settings related to the PWRTOGGLE CMD.

        **Keys in returned dict:**
            'CONST': Magic Constant (int).

        Returns:
            (:obj:`dict`): settings

        """
        return self.OPT_Config_File["PWRTOGGLE_settings"]

    def CCDFlushBadColumns_settings(self):
        """Returns settings related to the CCDFlushBadColumns CMD.

        **Keys in returned dict:**
            'CCDSEL': CCD select, 1 bit for each CCD (1..127). (int)

        Returns:
            (:obj:`dict`): settings

        """
        return self.OPT_Config_File["CCDFlushBadColumns_settings"]

    def CCDBadColumn_settings(self):
        """Returns settings related to CCDBadColumn CMD.

        **Keys in returned dict:**
            'CCDSEL': CCD select, 1 bit for each CCD (1..127). (int) \n
            'NBC': Number of uint16 in BC as a uint16. Big Endian. Maximum number is 63. (int) \n
            'BC': Bad Columns as a list of uint16 (4..2047).

        Returns:
            (:obj:`dict`): settings

        """
        return self.OPT_Config_File["CCDBadColumn_settings"]

    def PM_settings(self):
        """Returns settings related to the PM (photometer) CMD.

        **Keys in returned dict:**
            'TEXPMS': Exposure time [ms] for the photometer (int) \n
            'TEXPIMS': Exposure interval time [ms] for the photometer (int)

        Returns:
            (:obj:`dict`): settings

        """
        return self.OPT_Config_File["PM_settings"]

    def CCDBIAS_settings(self):
        """Returns settings related to the CCDBIAS CMD.

        **Keys in returned dict:**
            'CCDSEL': CCD select, 1 bit for each CCD (1..127). (int) \n
            'VGATE': 8-bit value representing a Voltage (int) \n
            'VSUBST': 8-bit value representing a Voltage (int) \n
            'VRD': 8-bit value representing a Voltage (int) \n
            'VOD': 8-bit value representing a Voltage (int) \n

        Returns:
            (:obj:`dict`): settings

        """
        return self.OPT_Config_File["CCDBIAS_settings"]

    """
    def HTR_settings():
        '''Returns settings related to the HTR CMD.

        **Keys in returned dict:**
            'HTRSEL': HTR select, 1 bit for each HTR (bits 0,1,6,7). (int) \n
            'SET': Heater set point (int) \n
            'PVALUE': Regulator Proportional constant (int) \n
            'IVALUE': Regulator Integral constant (int) \n
            'DVALUE': Regulator Derivative constant (int) \n

        Returns:
            (:obj:`dict`): settings

        '''
        settings = {'CCDSEL': 3, 'SET': 1402, 'PVALUE': 256, 'IVALUE': 10, 'DVALUE': 0}
        return settings
    """

    def CCD_macro_settings(self, CCDMacroSelect):
        """Returns CCD settings for a specific CCD macro.

        Each key in the output represents settings for a corresponding CCDSEL argument.
        TEXPIMS for the CCDs (except nadir) is not changeable as they need to be synchronized with a calculated TEXPIMS to prevent streaks. This is usually performed when macros are scheduled.

        **Keys in returned dict:**
            16: Represents settings for UV1 (CCD5) \n
            32: Represents settings for UV2 (CCD6) \n
            1: Represents settings for IR1 (CCD1) \n
            8: Represents settings for IR2 (CCD4) \n
            2: Represents settings for IR4 (CCD2) \n
            4: Represents settings for IR3 (CCD3) \n
            64: Represents settings for Nadir (CCD6) \n


        Arguments:
            CCDMacroSelect (str): Specifies for which CCD macro, settings are returned for. 'CustomBinning', 'HighResUV', 'HighResIR', 'BinnedCalibration', 'FullReadout', 'LowPixel'.

        Returns:
            (:obj:`dict`): CCD_settings

        """

        CCD_settings = {16: {}, 32: {}, 1: {}, 8: {}, 2: {}, 4: {}, 64: {}}
        CCD_settings[16] = self.OPT_Config_File["CCD_macro_settings"][CCDMacroSelect][
            "CCD_settings_UV1"
        ]
        CCD_settings[32] = self.OPT_Config_File["CCD_macro_settings"][CCDMacroSelect][
            "CCD_settings_UV2"
        ]
        CCD_settings[1] = self.OPT_Config_File["CCD_macro_settings"][CCDMacroSelect][
            "CCD_settings_IR1"
        ]
        CCD_settings[8] = self.OPT_Config_File["CCD_macro_settings"][CCDMacroSelect][
            "CCD_settings_IR2"
        ]
        CCD_settings[2] = self.OPT_Config_File["CCD_macro_settings"][CCDMacroSelect][
            "CCD_settings_IR3"
        ]
        CCD_settings[4] = self.OPT_Config_File["CCD_macro_settings"][CCDMacroSelect][
            "CCD_settings_IR4"
        ]
        CCD_settings[64] = self.OPT_Config_File["CCD_macro_settings"][CCDMacroSelect][
            "CCD_settings_Nadir"
        ]

        return CCD_settings

    def CheckConfigFile(self):
        """Checks the values of the settings in the *Configuration File* chosen with *Set_ConfigFile*.

        Also prints out the currently selected *Configuration File* and which starting date and TLE it currently uses.

        """
        from mats_planningtool.CheckConfigFile.Core import CheckConfigFile

        CheckConfigFile(self)

    def Timeline_gen(self):
        """Invokes the Timeline generator part of Operational Planning Tool.

        Creates a *Science Mode Timeline* as a .json file. \n
        Predicts and schedueles Science Modes that depend on certain events such as position of stars and the moon (Mode120-Mode124).
        Other Science Modes and StartUpCMDs are just scheduled at the start of the Timeline or at a given date.
        The Science Modes and StartUpCMDs to be scheduled are listed in *Modes_priority* in the chosen *Configuration File*.

        *Operational Science Modes* (example: Mode 1,2,5) are scheduled separately wherever time is available at the end of the program.

        Settings for the operation of the program are stated in the *Configuration File* chosen with *Set_ConfigFile*.

        Returns:
            None
        """
        from mats_planningtool.TimelineGenerator.Core import Timeline_generator

        Timeline_generator(self)

    def XML_gen(self, SCIMOD_Path=None):
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

        if SCIMOD_Path == None:
            SCIMOD_Path = os.path.join(
                "Output",
                "Science_Mode_Timeline_" + os.path.split(self.config_file_name)[1],
            )
        XML_TIMELINE = XML_generator(self, SCIMOD_Path)

        return XML_TIMELINE

    def Plot_Timeline_Plotter_Plots(
        self,
        FigureDirectory,
        FilesToPlot=[
            "ActiveScienceMode",
            "Yaw",
            "Pitch",
            "Roll",
            "Lat",
            "Long",
            "Alt",
            "ECEFerror",
            "PosError",
            "PosErrorRCI",
            "MagPosError",
            "Lat_LP",
            "Long_LP",
            "Alt_LP",
            "AltError_LP",
            "PosError_LP",
            "PosErrorRCI_LP",
            "MagPosError_LP",
            "RA_OpticalAxis",
            "RA_OpticalAxisError",
            "Dec_OpticalAxis",
            "Dec_OpticalAxisError",
            "PosErrorMATS_STK",
        ],
    ):
        """Plots binary files created with *Timeline_Plotter*.

        Tries to plot all files which are generated by default by *Timeline_Plotter* unless a second input is given.

        Arguments:
            FigureDirectory (str): Path to the directory where the binary files are located.
            FilesToPlot (list of str): Optional. List of strings containing the names of the binary files (excluding "fig.pickle") to be plotted.

        """

        from mats_planningtool.PlotTimelinePlotterPlots.Core import (
            Plot_Timeline_Plotter_Plots,
        )

        Plot_Timeline_Plotter_Plots(FigureDirectory, FilesToPlot)

    def MinimalScienceXML_gen(self):
        """Invokes the *MinimalScienceXML_gen* part of the *OPT*.

        Creates an .xml file with fixed CMDs which purpose is to define a flight procedure which is ran on the satellite
        following unscheduled power termination of the payload.
        Runs startup CMDs and sets the payload in operation mode with the CCD macro *HighResIR*.
        The CMD staggering is fixed. No date is given in the generated XML and will need to be added manually.
        Uses settings for the CMDs from the currently set *Configuration File*.

        """

        from mats_planningtool.XMLGenerator.MinimalScienceXML_gen import (
            MinimalScienceXMLGenerator,
        )

        MinimalScienceXMLGenerator(self)

    def Timeline_analyzer(self, science_mode_timeline_path, date):
        """Invokes the Timeline_analyser program part of Operational Planning Tool.

        Searches a Science Mode Timeline json file for a given date and returns the scheduled mode and its parameters.

        Arguments:
            science_mode_timeline_path (str): path to the .json file containing the Science Mode Timeline
            date (str): A given date and time ('2019/09/05 12:09:25')

        Returns:
            (tuple): tuple containing:

                **Mode** (*str*): The currently scheduled Mode ath the given date. \n
                **Parameters** (*dict*): The parameters of the Mode. \n
        """
        from mats_planningtool.TimelineAnalyzer.Core import Timeline_analyzer

        Mode, Parameters = Timeline_analyzer(science_mode_timeline_path, date)

        return Mode, Parameters

    def Timeline_Plotter(
        self,
        Science_Mode_Path,
        OHB_H5_Path="",
        STK_CSV_PATH="",
        Timestep=16,
        FractionOfDataUsed=0.1,
    ):
        """Invokes the *Timeline_Plotter* program part of *Operational_Planning_Tool*.

        Simulates the position and attitude of MATS from a given Science Mode Timeline and also optionally compares it to
        positional and attitude data given in a .h5 data set, located at *OHB_H5_Path*. Plots both the simulated data and given data.
        The attitude data shows only the target pointing orientation and does not mimic MATS's actual attitude control system. This leads to large pointing differences whenever the pointing altitude is changed. \n
        The timesteps of both the .h5 data and the Science Mode is synchronized to allow direct comparison if possible. \n

        A .csv file, generated in STK, may also be included to plot the predicted positional error of the satellite compared to STK data. Only data points with equal timestamps to the simulated Science Mode Timeline data will be plotted.
        Saves generated plots as binary files. \n

        Settings for the operation of the program are stated in the chosen *Configuration File*.
        Settings stated in the *Science Mode Timeline* override settings given in the chosen *Configuration file*.

        Arguments:
            Science_Mode_Path (str): Path to the Science Mode Timeline to be plotted.
            OHB_H5_Path (str): *Optional*. Path to the .h5 file containing position, time, and attitude data. The .h5 file is defined in the "Ground Segment ICD" document. The timestamps for the attitude and state data is assumed to be synchronized.
            STK_CSV_PATH (str): *Optional*. Path to the .csv file containing position (column 1-3), velocity (column 4-6), and time (column 7), generated in STK. Position and velocity data is assumed to be in km and in ICRF.
            Timestep (int): *Optional*. The chosen timestep of the Science Mode Timeline simulation [s]. Drastically changes runtime of the program.

        Returns:
            (tuple): tuple containing:

                - **Data_MATS** (*dict*): Dictionary containing lists of simulated data of MATS. \n
                - **Data_LP** (*dict*): Dictionary containing lists of simulated data of LP. \n
                - **Time** (*list*): List containing timestamps (utc) of the simulated data in Data_MATS and Data_LP. \n
                - **Time_OHB** (*list*): List containing timestamps (utc) of the plotted data in the .h5 file. \n


        """
        from mats_planningtool.TimelinePlotter.Core import Timeline_Plotter

        Data_MATS, Data_LP, Time, Time_OHB = Timeline_Plotter(
            Science_Mode_Path=Science_Mode_Path,
            configFile=self,
            OHB_H5_Path=OHB_H5_Path,
            STK_CSV_FILE=STK_CSV_PATH,
            Timestep=Timestep,
            FractionOfDataUsed=FractionOfDataUsed,
        )

        return Data_MATS, Data_LP, Time, Time_OHB

    def PLUTOGenerator(
        self,
        XML_Path=None,
        PLUTO_Path="Output/pluto_script.plp",
        wait_platform=False,
        max_wait_time=None,
    ):
        """Invokes PLUTO generator

        """

        from mats_planningtool.PLUTOGenerator import PLUTOGenerator

        if XML_Path is None:
            SCIMOD_Path = (
                "Output_"
                + "Science_Mode_Timeline_"
                + os.path.splitext(os.path.split(self.config_file_name)[1])[0]
            )
            print(SCIMOD_Path)
            XML_Path = os.path.join(
                "Output", "XML_TIMELINE__" + "FROM__" + SCIMOD_Path + ".xml"
            )

        PLUTOGenerator.PLUTO_generator(
            self, XML_Path, PLUTO_Path, wait_platform, max_wait_time
        )

        return
