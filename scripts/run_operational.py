#%%
from mats_planningtool import configFile as configFile
import datetime as DT
import requests as R
import glob
import json 
import xml.etree.ElementTree as ET
import os
import pandas as pd
import ast

def get_MATS_tle():
    query = 'https://celestrak.org/NORAD/elements/gp.php?CATNR=54227&FORMAT=tle'
    celestrak = R.session()
    tle = celestrak.get(query).text.split('\r\n')[1:3]
    print('using Mats tle \n',tle)
    if tle[0][1:5] == 'html':
        raise LookupError('Could not get TLE. Probably too many queries to celestrack, please wait 2 hours and try again.')
    return tle

def generate_operational_mode(startdate,duration,mode='1100',name='MODE1y',iterate=None,tle=None):

    if tle == None:
        tle = get_MATS_tle()

    configfile = configFile.configFile(
        "data/Operational/configfile_" + mode +"_" + name + ".json",
        DT.datetime.strftime(startdate,"%Y/%m/%d %H:%M:%S"),
        TLE1=tle[0],
        TLE2=tle[1],
    )


    hours = int(duration)
    minutes = (duration*60) % 60
    seconds_tot = int(((duration*3600) % 60) + minutes*60) 
    
    configfile.Timeline_settings()["duration"]["hours"] = hours
    configfile.Timeline_settings()["duration"]["seconds"] = seconds_tot
    configfile.set_duration()
    configfile.output_dir = "data/Operational_dump/"

    if iterate != None:
        configfile.OPT_Config_File["name"] = configfile.OPT_Config_File["name"] + iterate

    configfile.CheckConfigFile()    
    configfile.Timeline_gen()
    configfile.XML_gen()

    return

def generate_star_staring_mode(startdate,duration,mode='3040',name='STAR',iterate=None):

    tle = get_MATS_tle()    

    configfile = configFile.configFile(
        "data/Operational/configfile_" + mode + "_" + name + ".json",
        DT.datetime.strftime(startdate,"%Y/%m/%d %H:%M:%S"),
        TLE1=tle[0],
        TLE2=tle[1],
    )
    hours = int(duration)
    minutes = (duration*60) % 60
    seconds_tot = int(((duration*3600) % 60) + minutes*60) 
    
    configfile.Timeline_settings()["duration"]["hours"] = hours
    configfile.Timeline_settings()["duration"]["seconds"] = seconds_tot
    configfile.set_duration()


    configfile.Mode120_settings()['TimeToConsider']['hours'] = hours
    configfile.Mode120_settings()['TimeToConsider']['seconds'] = seconds_tot
    configfile.Mode120_settings()['TimeToConsider']['TimeToConsider'] = hours*3600 + seconds_tot

    configfile.set_duration()
    configfile.output_dir = "data/Operational_dump"

    if iterate != None:
        configfile.OPT_Config_File["name"] = configfile.OPT_Config_File["name"] + iterate

    configfile.CheckConfigFile()    
    configfile.Timeline_gen()
    configfile.XML_gen()

    return


def generate_fullframe_snapshot(startdate, mode='3200',name='FFEXP' , snapshottimes = [], exptimes = [3000,3000], altitude=92500, iterate = None):

    tle = get_MATS_tle()

    configfile = configFile.configFile(
        "data/Operational/configfile_" + mode + "_" + name + ".json",
        DT.datetime.strftime(startdate,"%Y/%m/%d %H:%M:%S"),
        TLE1=tle[0],
        TLE2=tle[1],
    )

    time_after_last_snapshot = DT.timedelta(minutes=15)
    endtime = snapshottimes[-1] + time_after_last_snapshot
    duration = endtime-startdate
    
    seconds_tot = duration.seconds

    configfile.Timeline_settings()["duration"]["hours"] = 0
    configfile.Timeline_settings()["duration"]["seconds"] = seconds_tot
    configfile.set_duration()
    configfile.SNAPSHOT_settings()["duration"] = seconds_tot - time_after_last_snapshot.seconds + 120


    configfile.output_dir = "data/Operational_dump/"

    configfile.SNAPSHOT_settings()['ExpTimes'] = exptimes
    if len(snapshottimes)==1:    
        configfile.SNAPSHOT_settings()['SnapshotTimes'] = [DT.datetime.strftime(snapshottimes[0],"%Y/%m/%d %H:%M:%S")]
    else:
        configfile.SNAPSHOT_settings()['SnapshotTimes'] = []
        for i in range(len(snapshottimes)):
            configfile.SNAPSHOT_settings()['SnapshotTimes'].append(DT.datetime.strftime(snapshottimes[i],"%Y/%m/%d %H:%M:%S"))


    if iterate != None:
        configfile.OPT_Config_File["name"] = configfile.OPT_Config_File["name"] + iterate

    configfile.CheckConfigFile()
    json_gen = True 
    xml_gen = True   
    if json_gen:
        configfile.Timeline_gen()
    if xml_gen:
        configfile.XML_gen()
    return configfile


def generate_rad_measurements(data_frame):
    n = 0

    for row in range(0, len(data_frame)):
        exptime = ast.literal_eval(data_frame.iloc[row].texpms)
        snaptimes = []
        snaptimes.append(data_frame.iloc[row].date)

        #if exptimes_current == exptime:
        #    snaptimes.append(data_frame.iloc[row].date)
        #else:
        starttime = snaptimes[0] - DT.timedelta(minutes=15)
        n = n+1
        generate_fullframe_snapshot(starttime, mode='3204',name='RAD' , exptimes = exptime, snapshottimes = snaptimes, altitude=-1, iterate=str(n))
        
    return

def generate_overview(folder: str):

    all_timelines = []
    #filenames = glob.glob("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/comissioning/**/Science_Mode_Timeline*.json", recursive=True)
    #filenames = glob.glob("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational/Science_Mode_Timeline*.json", recursive=True)
    filenames = glob.glob(folder + "Science_Mode_Timeline*.json", recursive=True)
    
    start_date_initial = None

    for i,filename in enumerate(filenames):
        with open(filename) as json_file:
            timeline = json.load(json_file)

        metadata=dict()
        generation_date = DT.datetime.strptime(timeline[0][3].split(' ')[2],'%Y/%m/%d')
        start_date =  DT.datetime.strptime(timeline[0][5]['start_date'],'%Y/%m/%d %H:%M:%S')
        end_date = start_date + DT.timedelta(seconds = timeline[0][5]['duration']['duration'])
        metadata["start_date"] = start_date
        if start_date_initial == None:
            start_date_initial = start_date
        if start_date<start_date_initial:
            start_date_initial = start_date

        metadata["end_date"] = end_date
        id = filename.split('/')[-1].split('_')[3]
        metadata["id"] = id
        name = filename.split('/')[-1].split('_')[4].split('.')[0][14:]
        metadata["name"] = name

        # if name=='RAY60':
        #     start_date =  DT.datetime(2022,11,28,14)
        #     end_date = start_date + DT.timedelta(seconds = timeline[0][5]['duration']['duration'])
        # elif name == 'RAY90':
        #     start_date =  DT.datetime(2022,11,28,17)
        #     end_date = start_date + DT.timedelta(seconds = timeline[0][5]['duration']['duration'])
        # elif name == 'RAY120':
        #     start_date =  DT.datetime(2022,11,28,20)
        #     end_date = start_date + DT.timedelta(seconds = timeline[0][5]['duration']['duration'])

        version = filename.split('/')[-1].split('_')[4].split('.')[0][12:14]
        metadata["version"] = version
        standard_altitude = timeline[0][5]["StandardPointingAltitude"]
        metadata["standard_altitude"] = standard_altitude
        metadata["yaw_correction"] = timeline[0][5]["yaw_correction"]
        pointing_altitudes = []
        description_long = []
        for i in range(1,len(timeline)):
            if "pointing_altitude" in timeline[i][3].keys():
                pointing_altitudes.append(timeline[i][3]['pointing_altitude'])
            if "Altitude" in timeline[i][3].keys():
                pointing_altitudes.append(timeline[i][3]['Altitude'])

            if timeline[i][0] == 'Mode120':
                description_long.append(timeline[i][4].split("Star name:")[1].split(",")[0])                


        metadata["pointing_altitudes"] = pointing_altitudes

        
        XML_name = '/'.join(filename.split('/')[:-1]) + '/' + 'STP-MTS-' + id + '_' + start_date.strftime('%y%m%d') + generation_date.strftime('%y%m%d') + version  + name + '.xml'
        xml_file_exists = os.path.isfile(XML_name)
        if not xml_file_exists:
            XML_name = '/'.join(filename.split('/')[:-1]) + '/' + 'STP-MTS-' + id + '_' + start_date.strftime('%y%m%d') + generation_date.strftime('%y%m%d') + version  + 'T' + name + '.xml'
            xml_file_exists = os.path.isfile(XML_name)

        if xml_file_exists:
            tree = ET.parse(XML_name)    
            root = tree.getroot()

            xml_startdate = DT.datetime.strptime(root[0][2][0].text,'%Y-%m-%dT%H:%M:%S')
            if not( xml_startdate == start_date):
                start_date = xml_startdate
                print('start date different from json')
            
            if root[-1][-1].attrib['mnemonic']=='TC_pafMODE':
                if root[-1][-1][2][0].text == '2':
                    end_date = start_date + DT.timedelta(seconds=int(root[-1][-1][0].text))
                    print('end date different from json')

            metadata["start_date"] = start_date
            metadata["end_date"] = end_date

            metadata["xml_file"] = XML_name.split("/")[-1]
            all_timelines.append(metadata) 
    
            metadata["description_short"] = ''
            metadata["description_long"] = description_long
        else:
            print('No xml found for ' + str(XML_name))

    all_timelines = sorted(all_timelines, key=lambda t: t["start_date"])
    df = pd.DataFrame(all_timelines)
    df.to_csv(folder + start_date_initial.strftime('%Y%m%d') + '_timeline_schedule.csv',index=False)

def read_snaptimes(filename):
    data_frame = pd.read_csv(filename,header=0)
    data_frame['date'] = pd.to_datetime(data_frame['date'])

    return data_frame
# generate_operational_mode(DT.datetime(2022,12,21,18,00),6)
# generate_operational_mode(DT.datetime(2022,12,22,18,00),9)
# generate_operational_mode(DT.datetime(2022,12,23,18,00),9)
# generate_operational_mode(DT.datetime(2022,12,24,18,00),9)
# generate_operational_mode(DT.datetime(2022,12,25,18,00),9)
# generate_operational_mode(DT.datetime(2022,12,26,18,00),9)
# generate_operational_mode(DT.datetime(2022,12,27,18,00),9)
# generate_operational_mode(DT.datetime(2022,12,28,18,00),9)
# generate_operational_mode(DT.datetime(2022,12,29,18,00),9)
# generate_operational_mode(DT.datetime(2022,12,30,18,00),6)
# generate_star_staring_mode(DT.datetime(2022,12,30,6,00),6)
# generate_operational_mode(DT.datetime(2022,12,31,18,00),12)
# generate_operational_mode(DT.datetime(2023,1,1,18,00),9)
# generate_operational_mode(DT.datetime(2023,1,2,18,00),12)
# generate_operational_mode(DT.datetime(2023,1,3,18,00),9)
# generate_operational_mode(DT.datetime(2023,1,4,18,00),12)


# generate_star_staring_mode(DT.datetime(2023,1,5,6,00),6)
# generate_operational_mode(DT.datetime(2023,1,5,18,00),6)
# generate_operational_mode(DT.datetime(2023,1,6,18,00),12,'1101')
# generate_operational_mode(DT.datetime(2023,1,7,18,00),12)
# generate_operational_mode(DT.datetime(2023,1,8,18,00),12)
# generate_operational_mode(DT.datetime(2023,1,9,18,00),12)
# generate_operational_mode(DT.datetime(2023,1,10,18,00),12)
# generate_operational_mode(DT.datetime(2023,1,11,18,00),12)

# generate_star_staring_mode(DT.datetime(2023,1,12,6,0,0),12,mode='3043')
# generate_star_staring_mode(DT.datetime(2023,1,13,6,0,0),12,mode='3043')
# generate_star_staring_mode(DT.datetime(2023,1,14,6,0,0),12,mode='3040')
# generate_star_staring_mode(DT.datetime(2023,1,15,6,0,0),12,mode='3043')
# generate_star_staring_mode(DT.datetime(2023,1,16,6,0,0),12,mode='3044')
# generate_star_staring_mode(DT.datetime(2023,1,17,6,0,0),12,mode='3044')
# generate_star_staring_mode(DT.datetime(2023,1,18,6,0,0),12,mode='3044')

# generate_operational_mode(DT.datetime(2023,1,12,18,00),9,'1101')
# generate_operational_mode(DT.datetime(2023,1,13,18,00),9)
# generate_operational_mode(DT.datetime(2023,1,14,18,00),9)
# generate_operational_mode(DT.datetime(2023,1,15,18,00),9)
# generate_operational_mode(DT.datetime(2023,1,16,18,00),9)
# generate_operational_mode(DT.datetime(2023,1,17,18,00),9)
# generate_operational_mode(DT.datetime(2023,1,18,18,00),9)


# generate_star_staring_mode(DT.datetime(2023,1,19,6,0,0),12,mode='3044')
# generate_star_staring_mode(DT.datetime(2023,1,20,6,0,0),12,mode='3044')
# generate_star_staring_mode(DT.datetime(2023,1,21,6,0,0),12,mode='3044')
# generate_star_staring_mode(DT.datetime(2023,1,22,6,0,0),12,mode='3044')

# generate_operational_mode(DT.datetime(2023,1,19,18,00),9)
# generate_operational_mode(DT.datetime(2023,1,20,18,00),9)
# generate_operational_mode(DT.datetime(2023,1,21,18,00),9)
# generate_operational_mode(DT.datetime(2023,1,22,18,00),9)
# generate_operational_mode(DT.datetime(2023,1,23,18,00),12)
# generate_operational_mode(DT.datetime(2023,1,24,18,00),12)
# generate_operational_mode(DT.datetime(2023,1,25,18,00),12)


#generate_fullframe_snapshot(DT.datetime(2023,1,26,8,00),mode='3201',name='CROPA',json_gen=True,xml_gen=False)
#generate_fullframe_snapshot(DT.datetime(2023,1,26,8,00),mode='3201',name='CROPA',json_gen=False,xml_gen=True)
#generate_fullframe_snapshot(DT.datetime(2023,1,26,10,00),mode='3202',name='CROPB',json_gen=True,xml_gen=False)
#generate_fullframe_snapshot(DT.datetime(2023,1,26,10,00),mode='3202',name='CROPB',json_gen=False,xml_gen=True)

# generate_operational_mode(DT.datetime(2023,1,26,18,00),6)
# generate_operational_mode(DT.datetime(2023,1,27,18,00),12)
#generate_star_staring_mode(DT.datetime(2023,1,28,6,0,0),2,mode='3040')
#generate_star_staring_mode(DT.datetime(2023,1,28,8,0,0),2,mode='3040')
# generate_operational_mode(DT.datetime(2023,1,29,18,00),9)
#generate_operational_mode(DT.datetime(2023,1,30,18,00),12,'1102',name='CROPA')
#generate_operational_mode(DT.datetime(2023,1,31,18,00),12,'1103',name='CROPB')
#generate_operational_mode(DT.datetime(2023,2,1,18,00),12)

#generate_fullframe_snapshot(DT.datetime(2023,2,2,8,00),mode='3203',name='CROPC',json_gen=True,xml_gen=False)
#generate_fullframe_snapshot(DT.datetime(2023,2,2,8,00),mode='3203',name='CROPC',json_gen=False,xml_gen=True)
# generate_operational_mode(DT.datetime(2023,2,2,18,00),12,'1104',name='CROPC')
# generate_operational_mode(DT.datetime(2023,2,3,18,00),23,'1104',name='CROPC')
# generate_operational_mode(DT.datetime(2023,2,4,18,00),23,'1104',name='CROPC')
# generate_operational_mode(DT.datetime(2023,2,5,18,00),23,'1104',name='CROPC')
# generate_operational_mode(DT.datetime(2023,2,6,18,00),23,'1104',name='CROPC')
# generate_operational_mode(DT.datetime(2023,2,7,18,00),23,'1104',name='CROPC')
# generate_operational_mode(DT.datetime(2023,2,8,18,00),12,'1104',name='CROPC')

#generate_star_staring_mode(DT.datetime(2023,2,13,8,0,0),2,mode='3045',name="MOON")
# generate_operational_mode(DT.datetime(2023,2,9,18,00),12,'1105',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,10,18,00),23,'1105',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,11,18,00),23,'1105',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,12,18,00),23,'1105',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,13,18,00),23,'1105',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,14,18,00),23,'1105',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,15,18,00),12,'1105',name='CROPD')

# generate_operational_mode(DT.datetime(2023,2,16,18,00),12,'1106',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,17,18,00),23,'1107',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,18,18,00),23,'1107',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,19,18,00),23,'1107',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,20,18,00),23,'1107',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,21,18,00),23,'1107',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,22,18,00),12,'1107',name='CROPD')

#generate_star_staring_mode(DT.datetime(2023,2,23,7,0,0),10,mode='3040')
# generate_operational_mode(DT.datetime(2023,2,23,18,00),23,'1107',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,24,18,00),23,'1107',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,25,18,00),23,'1107',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,26,18,00),23,'1107',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,27,18,00),23,'1107',name='CROPD')
# generate_operational_mode(DT.datetime(2023,2,28,18,00),23,'1107',name='CROPD')
# generate_operational_mode(DT.datetime(2023,3,1,18,00),12,'1107',name='CROPD')


# generate_star_staring_mode(DT.datetime(2023,3,2,6,0,0),6,mode='3042')
# generate_operational_mode(DT.datetime(2023,3,2,12,00),72,'1107',name='CROPD')
# generate_operational_mode(DT.datetime(2023,3,5,12,00),72,'1107',name='CROPD')
# generate_operational_mode(DT.datetime(2023,3,8,12,00),12,'1107',name='CROPD')

#generate_operational_mode(DT.datetime(2023,3,9,6,0),12,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,3,10,0,00),12,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,3,11,0,00),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,3,12,0,00),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,3,13,0,00),12,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,3,14,0,00),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,3,15,0,00),24,'1207',name='CROPD')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")


#generate_star_staring_mode(DT.datetime(2023,3,16,0,0,0),3,mode='3040',name='STRCRP')
# generate_operational_mode(DT.datetime(2023,3,16,3,00),21,'1207',name='CROPD')
# generate_operational_mode(DT.datetime(2023,3,17,0,00),72,'1207',name='CROPD')
# generate_operational_mode(DT.datetime(2023,3,20,0,00),72,'1207',name='CROPD')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")


#generate_operational_mode(DT.datetime(2023,3,23,0,0),72,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,3,26,0,0),48,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,3,28,12,0),36,'1207',name='CROPD')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")
# generate_star_staring_mode(DT.datetime(2023,3,28,0,0,0),2,mode='3046',name='MNCRP') 
# generate_star_staring_mode(DT.datetime(2023,3,28,5,0,0),2,mode='3045',name='MNCRP') 
# generate_star_staring_mode(DT.datetime(2023,3,28,8,0,0),2,mode='3047',name='MNCRP') 
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")


# generate_operational_mode(DT.datetime(2023,3,30,0,0),24,'1207',name='CROPD')
# generate_operational_mode(DT.datetime(2023,3,31,0,0),24,'1207',name='CROPD')
# generate_star_staring_mode(DT.datetime(2023,4,1,1,0),1,'3040',name='MARS')
# generate_operational_mode(DT.datetime(2023,4,1,3,0),21,'1207',name='CROPD') 
# generate_operational_mode(DT.datetime(2023,4,2,0,0),24,'1207',name='CROPD')
# generate_operational_mode(DT.datetime(2023,4,3,0,0),24,'1207',name='CROPD')
# generate_operational_mode(DT.datetime(2023,4,4,0,0),24,'1207',name='CROPD')
# generate_operational_mode(DT.datetime(2023,4,5,0,0),24,'1207',name='CROPD')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")


#generate_operational_mode(DT.datetime(2023,4,6,0,0),1.25,'1207',name='CROPD1')
#generate_star_staring_mode(DT.datetime(2023,4,6,1,30),0.5,'3040',name='MRSCRP1')
#generate_operational_mode(DT.datetime(2023,4,6,2,0),0.5,'3065',name='DRKBN1')
#generate_operational_mode(DT.datetime(2023,4,6,2,30),0.5,'3065',name='DRKBN2')
#generate_operational_mode(DT.datetime(2023,4,6,3,0),21,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,4,7,0,0),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,4,8,0,0),22.25,'1207',name='CROPD1')
#generate_star_staring_mode(DT.datetime(2023,4,8,22,40),0.5,'3040',name='MRSCRP2') 
#generate_operational_mode(DT.datetime(2023,4,8,23,15),24.75,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,4,10,0,0),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,4,11,0,0),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,4,12,0,0),24,'1207',name='CROPD')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")


# generate_operational_mode(DT.datetime(2023,4,13,0,0),24,'1207',name='CROPD')
# generate_operational_mode(DT.datetime(2023,4,14,0,0),24,'1207',name='CROPD')
# generate_operational_mode(DT.datetime(2023,4,15,0,0),24,'1207',name='CROPD')
# generate_operational_mode(DT.datetime(2023,4,16,0,0),24,'1207',name='CROPD')
# generate_operational_mode(DT.datetime(2023,4,17,0,0),24,'1207',name='CROPD')
# generate_operational_mode(DT.datetime(2023,4,18,0,0),24,'1207',name='CROPD')
# generate_operational_mode(DT.datetime(2023,4,19,0,0),24,'1207',name='CROPD')


#generate_star_staring_mode(DT.datetime(2023,4,20,0,0),6,'3040',name='STAR')
#generate_operational_mode(DT.datetime(2023,4,21,0,0),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,4,22,0,0),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,4,23,0,0),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,4,24,0,0),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,4,25,0,0),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,4,26,0,0),24,'1207',name='CROPD')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

#generate_operational_mode(DT.datetime(2023,4,27,3,0),2,'1107',name='CROPDN')
#generate_operational_mode(DT.datetime(2023,4,28,0,0),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,4,29,0,0),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,4,29,0,0),3,'1107',name='CROPDN')
#generate_operational_mode(DT.datetime(2023,4,29,3,0),21,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,4,30,0,0),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,5,1,0,0),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,5,2,0,0),24,'1207',name='CROPD')
#generate_operational_mode(DT.datetime(2023,5,3,0,0),24,'1207',name='CROPD')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

#generate_operational_mode(DT.datetime(2023,5,4,0,0),0.5,'3065',name='DRKBN1')
#generate_star_staring_mode(DT.datetime(2023,5,4,0,30),0.5,'3042',name='STAR')
#generate_operational_mode(DT.datetime(2023,5,4,1,0),2,'1108',name='CROPEN')
#generate_operational_mode(DT.datetime(2023,5,4,3,0),2,'1109',name='CROPFN')
#generate_operational_mode(DT.datetime(2023,5,4,5,0),19,'1107',name='CROPDN')
# generate_operational_mode(DT.datetime(2023,5,5,0,0),24,'1107',name='CROPDN')
# generate_operational_mode(DT.datetime(2023,5,6,0,0),24,'1107',name='CROPDN')
# generate_operational_mode(DT.datetime(2023,5,7,0,0),24,'1107',name='CROPDN')
# generate_operational_mode(DT.datetime(2023,5,8,0,0),24,'1107',name='CROPDN')
# generate_operational_mode(DT.datetime(2023,5,9,0,0),24,'1107',name='CROPDN')
# generate_operational_mode(DT.datetime(2023,5,10,0,0),24,'1107',name='CROPDN')
#generate_operational_mode(DT.datetime(2023,5,9,16,0),8,'1107',name='CROPDN')
#generate_operational_mode(DT.datetime(2023,5,9,0,0),6,'1107',name='CROPDN1')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")


# generate_operational_mode(DT.datetime(2023,5,11,0,0),11.1,'1109',name='CROPFN')
# generate_star_staring_mode(DT.datetime(2023,5,11,11,10,0),0.5,mode='3045',name="MOON")
# generate_operational_mode(DT.datetime(2023,5,11,11,40),2.6,'1109',name='CROPFN',iterate="1")
# generate_star_staring_mode(DT.datetime(2023,5,11,14,23,0),0.5,mode='3045',name="MOON",iterate="1")
# generate_operational_mode(DT.datetime(2023,5,11,14,53),1,'1109',name='CROPFN',iterate="2")
# generate_star_staring_mode(DT.datetime(2023,5,11,16,00,0),0.5,mode='3045',name="MOON",iterate="2")
# generate_operational_mode(DT.datetime(2023,5,11,16,30),7.5,'1109',name='CROPFN',iterate="3")
# generate_operational_mode(DT.datetime(2023,5,12,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,5,13,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,5,14,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,5,15,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,5,16,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,5,17,0,0),24,'1109',name='CROPFN')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

# generate_operational_mode(DT.datetime(2023,5,16,0,0),6,'1109',name='CROPFN',iterate="1")
# generate_operational_mode(DT.datetime(2023,5,16,6,0),6,'1109',name='CROPFN',iterate="2")
# generate_operational_mode(DT.datetime(2023,5,16,12,0),6,'1109',name='CROPFN',iterate="3")
# generate_operational_mode(DT.datetime(2023,5,16,18,0),6,'1109',name='CROPFN',iterate="4")

# generate_operational_mode(DT.datetime(2023,5,17,0,0),6,'1109',name='CROPFN',iterate="1")
# generate_operational_mode(DT.datetime(2023,5,17,6,0),6,'1109',name='CROPFN',iterate="2")
# generate_operational_mode(DT.datetime(2023,5,17,12,0),6,'1109',name='CROPFN',iterate="3")
# generate_operational_mode(DT.datetime(2023,5,17,18,0),6,'1109',name='CROPFN',iterate="4")

# tle = get_MATS_tle()
# generate_operational_mode(DT.datetime(2023,5,18,0,0),6,'1109',name='CROPFN',iterate="1",tle=tle)
# generate_operational_mode(DT.datetime(2023,5,18,6,0),6,'1109',name='CROPFN',iterate="2",tle=tle)
# generate_operational_mode(DT.datetime(2023,5,18,12,0),6,'1109',name='CROPFN',iterate="3",tle=tle)
# generate_operational_mode(DT.datetime(2023,5,18,18,0),6,'1109',name='CROPFN',iterate="4",tle=tle)

# generate_operational_mode(DT.datetime(2023,5,19,0,0),5.95,'1109',name='CROPFN',iterate="1",tle=tle)
#generate_operational_mode(DT.datetime(2023,5,19,6,0),6,'1109',name='CROPFN',iterate="2",tle=tle)
#generate_operational_mode(DT.datetime(2023,5,19,12,0),6,'1109',name='CROPFN',iterate="3",tle=tle)
# generate_operational_mode(DT.datetime(2023,5,19,18,0),5.95,'1109',name='CROPFN',iterate="4",tle=tle)

# generate_operational_mode(DT.datetime(2023,5,20,0,0),24,'1109',name='CROPFN',tle=tle)
# generate_operational_mode(DT.datetime(2023,5,21,0,0),24,'1109',name='CROPFN',tle=tle)
# generate_operational_mode(DT.datetime(2023,5,22,0,0),24,'1109',name='CROPFN',tle=tle)


#generate_operational_mode(DT.datetime(2023,5,30,0,0),2,'1109',name='CROPFN')



# generate_operational_mode(DT.datetime(2023,7,17,0,0),48,'1109',name='CROPFN')
#generate_operational_mode(DT.datetime(2023,7,19,0,0),15.5,'1109',name='CROPFN')
#generate_star_staring_mode(DT.datetime(2023,7,19,15,45),1,'3040',name='STAR')
#generate_operational_mode(DT.datetime(2023,7,19,17,0),7,'1109',name='CROPFN',iterate="1")
# generate_operational_mode(DT.datetime(2023,7,21,0,0),48,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,7,23,0,0),48,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,7,25,0,0),48,'1109',name='CROPFN')

# generate_operational_mode(DT.datetime(2023,7,27,0,0),48,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,7,29,0,0),48,'1109',name='CROPFN')
#generate_operational_mode(DT.datetime(2023,7,31,0,0),47.9,'1109',name='CROPFN')
#generate_operational_mode(DT.datetime(2023,8,2,0,0),48,'1109',name='CROPFN')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

# generate_operational_mode(DT.datetime(2023,7,27,0,0),0.5,'1109',name='CROPFN')
# generate_star_staring_mode(DT.datetime(2023,7,27,0,30),1,'3040',name='STAR')
# generate_operational_mode(DT.datetime(2023,7,27,1,30),46.5,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,7,29,0,0),48,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,7,31,0,0),47.9,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,8,2,0,0),48,'1109',name='CROPFN')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

#generate_operational_mode(DT.datetime(2023,8,4,0,0),48,'1109',name='CROPFN')
#generate_operational_mode(DT.datetime(2023,8,6,0,0),12,'1109',name='CROPFN')
#generate_star_staring_mode(DT.datetime(2023,8,6,12,0),2,'3040',name='JUPITER')
#generate_operational_mode(DT.datetime(2023,8,6,14,0),10,'1109',name='CROPFN',iterate="1")
#generate_operational_mode(DT.datetime(2023,8,7,0,0),27,'1109',name='CROPFN')
#generate_star_staring_mode(DT.datetime(2023,8,8,3,0),2,'3040',name='JUPITER')
#generate_operational_mode(DT.datetime(2023,8,8,5,0),33,'1109',name='CROPFN')
#generate_star_staring_mode(DT.datetime(2023,8,9,14,0),2,'3040',name='JUPITER')
#generate_operational_mode(DT.datetime(2023,8,9,16,0),32,'1109',name='CROPFN')


#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

# generate_operational_mode(DT.datetime(2023,8,4,12,0),36,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,8,4,18,0),30,'1109',name='CROPFN',iterate="1")
# generate_operational_mode(DT.datetime(2023,8,5,0,0),24,'1109',name='CROPFN',iterate="2")

# snaptimes = [
#     DT.datetime(2023,8,11,1,58,0),
#     DT.datetime(2023,8,11,4,58,0),
#     DT.datetime(2023,8,12,2,5,0),
#     DT.datetime(2023,8,12,5,4,0),
#     DT.datetime(2023,8,13,2,11,0),
#     DT.datetime(2023,8,13,5,10,0),
#     DT.datetime(2023,8,14,2,17,0),
#     DT.datetime(2023,8,14,5,16,0),
# ]


# n = 0
# for snaptime in snaptimes:
#     starttime = snaptime - DT.timedelta(minutes=20)
#     generate_fullframe_snapshot(starttime, mode='3204',name='RAD' , exptimes = [15000,15000],snapshottimes = [snaptime], altitude=-1 ,iterate=str(n))
#     n = n+1

# snaptimes = [
#     DT.datetime(2023,8,11,9,7,0),
#     DT.datetime(2023,8,12,9,13,0),
#     DT.datetime(2023,8,13,9,19,0),
#     DT.datetime(2023,8,14,9,26,0),
# ]

# for snaptime in snaptimes:
#     starttime = snaptime - DT.timedelta(minutes=20)
#     generate_fullframe_snapshot(starttime, mode='3204',name='RAD' , exptimes = [3000,3000],snapshottimes = [snaptime], altitude=-1 ,iterate=str(n))
#     n = n+1

#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

# data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/predict_0815.txt')
# n = 0
# for row in range(len(data_frame)):
#     snaptime = DT.datetime.strptime(data_frame.iloc[row].date,"%Y-%m-%d %H:%M:%S")
#     exptimes = ast.literal_eval(data_frame.iloc[row].texpms)
#     starttime = snaptime - DT.timedelta(minutes=20)
#     generate_fullframe_snapshot(starttime, mode='3204',name='RAD' , exptimes = exptimes,snapshottimes = [snaptime], altitude=-1 ,iterate=str(n))
#     n = n+1

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

# generate_operational_mode(DT.datetime(2023,8,24,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,8,25,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,8,26,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,8,27,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,8,28,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,8,29,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,8,30,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2023,8,31,0,0),24,'1109',name='CROPFN')

#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

# #%%
# data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/predict_230823.txt')

# n = 0
# for row in range(len(data_frame)):
#     snaptime = DT.datetime.strptime(data_frame.iloc[row].date,"%Y-%m-%d %H:%M:%S")
#     exptimes = ast.literal_eval(data_frame.iloc[row].texpms)
#     starttime = snaptime - DT.timedelta(minutes=20)
#     generate_fullframe_snapshot(starttime, mode='3204',name='RAD' , exptimes = exptimes,snapshottimes = [snaptime], altitude=-1 ,iterate=str(n))
#     n = n+1

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

#%%

# data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/predict_230828.txt')

# exptimes_current = ast.literal_eval(data_frame.iloc[0].texpms)
# snaptimes = [data_frame.iloc[0].date]
# n = 0

# for row in range(1, len(data_frame)):
#     exptime = ast.literal_eval(data_frame.iloc[row].texpms)
#     if exptimes_current == exptime:
#         snaptimes.append(data_frame.iloc[row].date)
#     else:
#         starttime = snaptimes[0] - DT.timedelta(minutes=15)
#         n = n+1
#         generate_fullframe_snapshot(starttime, mode='3204',name='RAD' , exptimes = exptimes_current, snapshottimes = snaptimes, altitude=-1, iterate=str(n))
        
#         snaptimes = []
#         snaptimes.append(data_frame.iloc[row].date)
#         exptimes_current = exptime


# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")


# #%%
# data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/predict_mats_230905.txt')

# exptimes_current = ast.literal_eval(data_frame.iloc[0].texpms)
# snaptimes = [data_frame.iloc[0].date]
# n = 0

# for row in range(1, len(data_frame)):
#     exptime = ast.literal_eval(data_frame.iloc[row].texpms)
#     if exptimes_current == exptime:
#         snaptimes.append(data_frame.iloc[row].date)
#     else:
#         starttime = snaptimes[0] - DT.timedelta(minutes=15)
#         n = n+1
#         generate_fullframe_snapshot(starttime, mode='3204',name='RAD' , exptimes = exptimes_current, snapshottimes = snaptimes, altitude=-1, iterate=str(n))
        
#         snaptimes = []
#         snaptimes.append(data_frame.iloc[row].date)
#         exptimes_current = exptime


# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")


#%%
# data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/predict_mats_230915.txt')
# generate_rad_measurements(data_frame)
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

# %%
# data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/predict_mats_230925.txt')
# generate_rad_measurements(data_frame)
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")


#generate_star_staring_mode(DT.datetime(2023,10,6,0,0),2,'3040',name='STARALL')
#generate_star_staring_mode(DT.datetime(2023,10,6,6,0),2,'3040',name='STARALL',iterate='1')
#generate_star_staring_mode(DT.datetime(2023,10,6,6,0),2,'3040',name='STARALL',iterate='2')
#data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/predict_mats_231008.txt')
#generate_rad_measurements(data_frame)
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")


# #%%
# generate_operational_mode(DT.datetime(2023,10,30,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,10,31,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,1,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,2,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,3,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,4,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,5,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,6,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,7,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,8,0,0),24,'1109',name='CROPFS')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")


# #%%
# generate_operational_mode(DT.datetime(2023,11,9,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,10,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,11,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,12,0,0),23.95,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,13,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,14,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,15,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,16,0,0),24,'1109',name='CROPFS')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")


# #%%
# generate_operational_mode(DT.datetime(2023,11,17,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,18,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,19,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,20,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,21,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,22,0,0),23.9,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,23,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,24,0,0),24,'1109',name='CROPFS')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")


#%%
# generate_operational_mode(DT.datetime(2023,11,25,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,26,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,27,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,28,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,29,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,11,30,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,1,0,0),24,'1109',name='CROPFS')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")
# #%%
# generate_operational_mode(DT.datetime(2023,12,2,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,3,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,4,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,5,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,6,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,7,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,8,0,0),24,'1109',name='CROPFS')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

#%%
# generate_operational_mode(DT.datetime(2023,12,9,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,10,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,11,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,12,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,13,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,14,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,15,0,0),24,'1109',name='CROPFS')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

#%%
#generate_operational_mode(DT.datetime(2023,12,16,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,17,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,18,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,19,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,20,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,21,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,22,0,0),24,'1109',name='CROPFS')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")


#data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational/predict_mats_231212.txt')
#generate_rad_measurements(data_frame)
# generate_operational_mode(DT.datetime(2023,12,24,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,28,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2023,12,30,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,1,2,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,1,5,0,0),24,'1109',name='CROPFS')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")



# data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational/predict_mats_240102.txt')
# generate_rad_measurements(data_frame)
# generate_operational_mode(DT.datetime(2024,1,8,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,1,10,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,1,12,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,1,14,0,0),24,'1109',name='CROPFA')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

#data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational/predict_mats_240105.txt')
#generate_rad_measurements(data_frame)
#generate_operational_mode(DT.datetime(2024,1,16,0,0),24,'1109',name='CROPFA')
#generate_operational_mode(DT.datetime(2024,1,17,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,1,19,0,0),23.95,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,1,20,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,1,22,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,1,23,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,1,25,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,1,26,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,1,28,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,1,29,0,0),24,'1109',name='CROPFA')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

#data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational/predict_mats_240123.txt')
#generate_rad_measurements(data_frame)
#generate_operational_mode(DT.datetime(2024,1,30,0,0),24,'1109',name='CROPFA')
#generate_operational_mode(DT.datetime(2024,1,31,0,0),24,'1109',name='CROPFA')
#generate_operational_mode(DT.datetime(2024,2,1,0,0),23.95,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,2,2,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,2,3,0,0),24,'1109',name='CROPFA')
# #generate_operational_mode(DT.datetime(2024,2,4,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,2,5,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,2,6,0,0),24,'1109',name='CROPFA')
# #generate_operational_mode(DT.datetime(2024,2,7,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,2,8,0,0),24,'1109',name='CROPFA')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

# data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational/predict_mats_240205.txt')
# generate_rad_measurements(data_frame)
# generate_operational_mode(DT.datetime(2024,2,10,0,0),23.95,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,2,13,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,2,16,0,0),24,'1109',name='CROPFA')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")

#data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational/predict_mats_240220.txt')
# #generate_rad_measurements(data_frame)
# generate_operational_mode(DT.datetime(2024,2,24,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,2,27,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,3,4,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,3,7,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,3,10,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,3,13,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,3,16,0,0),24,'1109',name='CROPFA')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")

#%%

# data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational/predict_mats_240318.txt')
# generate_rad_measurements(data_frame)
# generate_operational_mode(DT.datetime(2024,3,30,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,4,2,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,4,5,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,4,8,0,0),24,'1109',name='CROPFA')
#generate_operational_mode(DT.datetime(2024,4,11,0,0),24,'1109',name='CROPFA')
#generate_operational_mode(DT.datetime(2024,4,14,0,0),24,'1109',name='CROPFA')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


#%%
# data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational/predict_mats_240425.txt')
# generate_rad_measurements(data_frame)
# generate_operational_mode(DT.datetime(2024,4,27,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,4,30,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,5,3,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,5,6,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,5,9,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,5,12,0,0),24,'1109',name='CROPFA')

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")

#%%
# generate_operational_mode(DT.datetime(2024,5,20,18,0),6,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,5,21,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,5,22,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,5,23,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,5,24,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,5,25,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,5,26,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,5,27,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,5,28,0,0),24,'1109',name='CROPFA')

#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")

# %%
# generate_operational_mode(DT.datetime(2024,5,29,0,0),6,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,5,30,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,5,31,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,6,1,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,6,2,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,6,3,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,6,4,0,0),24,'1109',name='CROPFA')
# generate_operational_mode(DT.datetime(2024,6,5,0,0),24,'1109',name='CROPFA')

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# %%
# generate_operational_mode(DT.datetime(2024,6,8,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,6,9,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,6,10,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,6,11,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,6,12,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,6,13,0,0),24,'1109',name='CROPFN')

# %%
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")

# %%
# # %%
# generate_operational_mode(DT.datetime(2024,6,14,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,6,15,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,6,16,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,6,17,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,6,18,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,6,19,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,6,20,0,0),24,'1109',name='CROPFN')

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")

# # %%
# generate_operational_mode(DT.datetime(2024,6,21,0,0),24,'1109',name='CROPFN')
# #generate_operational_mode(DT.datetime(2024,6,22,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,6,23,0,0),24,'1109',name='CROPFN')
# #generate_operational_mode(DT.datetime(2024,6,24,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,6,25,0,0),24,'1109',name='CROPFN')
# #generate_operational_mode(DT.datetime(2024,6,26,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,6,27,0,0),24,'1109',name='CROPFN')

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# # %%
# #generate_operational_mode(DT.datetime(2024,6,28,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,6,29,0,0),24,'1109',name='CROPFN')
# #generate_operational_mode(DT.datetime(2024,6,30,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,7,1,0,0),24,'1109',name='CROPFN')
# #generate_operational_mode(DT.datetime(2024,7,2,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,7,3,0,0),24,'1109',name='CROPFN')
# #generate_operational_mode(DT.datetime(2024,7,4,0,0),24,'1109',name='CROPFN')

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# # %%
# generate_operational_mode(DT.datetime(2024,7,5,0,0),24,'1109',name='CROPFN')
# #generate_operational_mode(DT.datetime(2024,7,6,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,7,7,0,0),24,'1109',name='CROPFN')
# #generate_operational_mode(DT.datetime(2024,7,8,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,7,9,0,0),24,'1109',name='CROPFN')
# #generate_operational_mode(DT.datetime(2024,7,10,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,7,11,0,0),24,'1109',name='CROPFN')

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# %%
#generate_operational_mode(DT.datetime(2024,7,13,0,0),24,'1109',name='CROPFN')
#generate_operational_mode(DT.datetime(2024,7,15,0,0),24,'1109',name='CROPFN')
#generate_operational_mode(DT.datetime(2024,7,17,0,0),24,'1109',name='CROPFN')
#generate_operational_mode(DT.datetime(2024,7,19,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,7,21,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,7,23,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,7,25,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,7,27,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,7,29,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,7,31,0,0),24,'1109',name='CROPFN')

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# %%
# generate_operational_mode(DT.datetime(2024,8,2,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,4,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,6,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,8,0,0),24,'1109',name='CROPFN')

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")

# #%%
# generate_operational_mode(DT.datetime(2024,8,10,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,11,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,12,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,13,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,14,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,15,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,16,0,0),24,'1109',name='CROPFN')

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# #%%
# generate_operational_mode(DT.datetime(2024,8,17,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,18,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,19,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,20,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,21,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,22,0,0),24,'1109',name='CROPFN')

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# generate_operational_mode(DT.datetime(2024,8,24,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,25,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,26,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,27,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,28,0,0),24,'1109',name='CROPFN')

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# generate_operational_mode(DT.datetime(2024,8,29,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,30,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,8,31,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,9,1,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,9,2,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,9,3,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,9,4,0,0),24,'1109',name='CROPFN')

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# generate_operational_mode(DT.datetime(2024,9,12,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,9,13,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,9,14,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,9,15,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,9,16,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,9,17,0,0),24,'1109',name='CROPFN')

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")



# generate_operational_mode(DT.datetime(2024,9,21,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,9,22,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,9,23,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,9,24,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,9,25,0,0),24,'1109',name='CROPFN')
# generate_operational_mode(DT.datetime(2024,9,26,0,0),24,'1109',name='CROPFN')

# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")

# generate_operational_mode(DT.datetime(2024,9,28,10,0),12,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,9,29,10,0),12,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,9,30,10,0),12,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,10,1,10,0),12,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,10,2,10,0),12,'1209',name='ALTTEST')


# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# generate_operational_mode(DT.datetime(2024,10,3,10,0),12,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,10,4,10,0),12,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,10,5,10,0),12,'1209',name='ALTTEST')


# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")

# generate_operational_mode(DT.datetime(2024,10,6,10,0),12,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,10,7,10,0),12,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,10,8,10,0),12,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,10,9,10,0),12,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,10,10,10,0),12,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,10,11,10,0),12,'1209',name='ALTTEST')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# generate_operational_mode(DT.datetime(2024,10,12,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,10,13,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,10,14,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,10,15,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,10,16,8,0),16,'1209',name='ALTTEST')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")

#generate_operational_mode(DT.datetime(2024,10,17,8,0),16,'1209',name='ALTTEST')
#generate_operational_mode(DT.datetime(2024,10,18,8,0),16,'1209',name='ALTTEST')
#generate_operational_mode(DT.datetime(2024,10,19,8,0),16,'1209',name='ALTTEST')
#generate_operational_mode(DT.datetime(2024,10,20,8,0),16,'1209',name='ALTTEST')
#generate_operational_mode(DT.datetime(2024,10,21,8,0),16,'1209',name='ALTTEST')
#generate_operational_mode(DT.datetime(2024,10,22,8,0),16,'1209',name='ALTTEST')
#generate_operational_mode(DT.datetime(2024,10,23,8,0),16,'1209',name='ALTTEST')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")

#generate_operational_mode(DT.datetime(2024,10,24,8,0),24,'1109',name='CROPFS')
#generate_operational_mode(DT.datetime(2024,10,25,8,0),24,'1109',name='CROPFS')
#generate_operational_mode(DT.datetime(2024,10,26,8,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,10,27,8,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,10,28,8,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,10,29,8,0),24,'1109',name='CROPFS')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# generate_operational_mode(DT.datetime(2024,11,1,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,2,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,3,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,4,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,5,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,6,8,0),16,'1209',name='ALTTEST')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# generate_operational_mode(DT.datetime(2024,11,7,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,8,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,9,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,10,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,11,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,12,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,13,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,14,8,0),16,'1209',name='ALTTEST')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


#%% generate overview of entire mission (operational)
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational/")


# generate_operational_mode(DT.datetime(2024,11,15,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,16,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,17,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,18,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,19,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,20,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,21,8,0),16,'1209',name='ALTTEST')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")



# generate_operational_mode(DT.datetime(2024,11,22,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,23,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,24,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,25,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,26,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,27,8,0),16,'1209',name='ALTTEST')
# generate_operational_mode(DT.datetime(2024,11,28,8,0),16,'1209',name='ALTTEST')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# generate_operational_mode(DT.datetime(2024,11,29,8,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,11,30,8,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,1,8,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,2,8,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,3,8,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,4,8,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,5,8,0),24,'1109',name='CROPFS')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# generate_operational_mode(DT.datetime(2024,12,6,8,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,7,8,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,8,8,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,9,8,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,10,8,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,11,8,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,12,8,0),24,'1109',name='CROPFS')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/rad_measurements_24_12_13.txt')
# generate_rad_measurements(data_frame)
# generate_operational_mode(DT.datetime(2024,12,14,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,15,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,16,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,17,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,18,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,19,0,0),24,'1109',name='CROPFS')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")

#data_frame = read_snaptimes('/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/rad_measurements_24_12_13.txt')
# generate_rad_measurements(data_frame)
# generate_operational_mode(DT.datetime(2024,12,14,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,15,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,16,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,17,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,18,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,19,0,0),24,'1109',name='CROPFS')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")




#generate_operational_mode(DT.datetime(2024,12,24,0,0),24,'1109',name='CROPFS')
#generate_operational_mode(DT.datetime(2024,12,25,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,26,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,28,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,29,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,30,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2024,12,31,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,2,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,3,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,4,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,6,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,7,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,8,0,0),24,'1109',name='CROPFS')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# generate_operational_mode(DT.datetime(2025,1,16,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,17,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,18,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,19,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,20,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,21,0,0),24,'1109',name='CROPFS')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")

#generate_operational_mode(DT.datetime(2025,1,23,10,30),19,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,24,8,30),23,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,25,8,30),23,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,26,8,30),23,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,27,8,30),23,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,28,8,30),23,'1109',name='CROPFS')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# generate_operational_mode(DT.datetime(2025,1,30,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,1,31,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,1,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,2,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,3,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,4,0,0),24,'1109',name='CROPFS')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


#generate_operational_mode(DT.datetime(2025,2,6,0,0),24,'1109',name='CROPFS')
#generate_operational_mode(DT.datetime(2025,2,7,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,8,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,9,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,10,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,11,0,0),24,'1109',name='CROPFS')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")



# generate_operational_mode(DT.datetime(2025,2,15,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,16,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,17,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,18,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,19,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,20,0,0),24,'1109',name='CROPFS')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")


# generate_operational_mode(DT.datetime(2025,2,24,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,25,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,26,0,0),24,'1109',name='CROPFS')
# generate_operational_mode(DT.datetime(2025,2,27,0,0),24,'1109',name='CROPFS')
# generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")

generate_operational_mode(DT.datetime(2025,3,3,0,0),24,'1109',name='CROPFS')
generate_operational_mode(DT.datetime(2025,3,4,0,0),24,'1109',name='CROPFS')
generate_operational_mode(DT.datetime(2025,3,5,0,0),24,'1109',name='CROPFS')
generate_operational_mode(DT.datetime(2025,3,6,0,0),24,'1109',name='CROPFS')
generate_operational_mode(DT.datetime(2025,3,7,0,0),24,'1109',name='CROPFS')
generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool-bak/data/Operational_dump/")