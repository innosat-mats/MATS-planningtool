import datetime as DT
import json
import glob
import pandas as pd
import xml.etree.ElementTree as ET
import os

all_timelines = []
filenames = glob.glob("/home/olemar/Projects/Universitetet/MATS/MATS-planningtool/data/comissioning/**/Science_Mode_Timeline*.json", recursive=True)

for i,filename in enumerate(filenames):
    with open(filename) as json_file:
        timeline = json.load(json_file)

    metadata=dict()
    generation_date = DT.datetime.strptime(timeline[0][3].split(' ')[2],'%Y/%m/%d')
    start_date =  DT.datetime.strptime(timeline[0][5]['start_date'],'%Y/%m/%d %H:%M:%S')
    end_date = start_date + DT.timedelta(seconds = timeline[0][5]['duration']['duration'])
    metadata["start_date"] = start_date
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
    for i in range(1,len(timeline)):
        if "pointing_altitude" in timeline[i][3].keys():
            pointing_altitudes.append(timeline[i][3]['pointing_altitude'])
        if "Altitude" in timeline[i][3].keys():
            pointing_altitudes.append(timeline[i][3]['Altitude'])

    metadata["pointing_altitudes"] = pointing_altitudes
    
    XML_name = '/'.join(filename.split('/')[:-1]) + '/' + 'STP-MTS-' + id + '_' + start_date.strftime('%y%m%d') + generation_date.strftime('%y%m%d') + version  + name + '.xml'
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
    
    else:
        print('No xml found for ' + str(XML_name))

all_timelines = sorted(all_timelines, key=lambda t: t["start_date"])

# for i in range(len(all_timelines)):
#     all_timelines[i]["start_date"] = all_timelines[i]["start_date"].strftime('%Y-%m-%dT%H:%M:%SZ')
#     all_timelines[i]["end_date"] = all_timelines[i]["end_date"].strftime('%Y-%m-%dT%H:%M:%SZ')

df = pd.DataFrame(all_timelines)
df.to_csv('timeline_schedule.csv',index=False)

    