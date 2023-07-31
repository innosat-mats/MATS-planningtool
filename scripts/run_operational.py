from mats_planningtool import configFile as configFile
import datetime as DT
import requests as R
import glob
import json 
import xml.etree.ElementTree as ET
import os
import pandas as pd

def get_MATS_tle():
    query = 'https://celestrak.org/NORAD/elements/gp.php?CATNR=54227&FORMAT=tle'
    celestrak = R.session()
    tle = celestrak.get(query).text.split('\r\n')[1:3]
    print('using Mats tle \n',tle)
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
    configfile.output_dir = "data/Operational_dump/"

    if iterate != None:
        configfile.OPT_Config_File["name"] = configfile.OPT_Config_File["name"] + iterate

    configfile.CheckConfigFile()    
    configfile.Timeline_gen()
    configfile.XML_gen()

    return


def generate_fullframe_snapshot(startdate,mode='3200',name='FFEXP',altitude=92500,json_gen=True,xml_gen=True):

    tle = get_MATS_tle()

    configfile = configFile.configFile(
        "data/Operational/configfile_" + mode + "_" + name + ".json",
        DT.datetime.strftime(startdate,"%Y/%m/%d %H:%M:%S"),
        TLE1=tle[0],
        TLE2=tle[1],
    )
    configfile.set_duration()
    configfile.output_dir = "data/Operational_dump/"
    configfile.CheckConfigFile()    
    if json_gen:
        configfile.Timeline_gen()
    if xml_gen:
        configfile.XML_gen()
    return configfile



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
#generate_operational_mode(DT.datetime(2023,8,6,0,0),48,'1109',name='CROPFN')
generate_star_staring_mode(DT.datetime(2023,8,6,12,0),2,'3040',name='JUPITER')
#generate_operational_mode(DT.datetime(2023,8,6,0,0),48,'1109',name='CROPFN')
#generate_operational_mode(DT.datetime(2023,8,8,0,0),48,'1109',name='CROPFN')
generate_star_staring_mode(DT.datetime(2023,8,8,3,0),2,'3040',name='JUPITER')
#generate_overview("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/Operational_dump/")