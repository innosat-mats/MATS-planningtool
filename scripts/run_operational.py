from mats_planningtool import configFile as configFile
import datetime as DT
import requests as R

def get_MATS_tle():
    query = 'https://celestrak.org/NORAD/elements/gp.php?CATNR=54227&FORMAT=tle'
    celestrak = R.session()
    tle = celestrak.get(query).text.split('\r\n')[1:3]
    print('using Mats tle \n',tle)
    return tle

def generate_operational_mode(startdate,duration,mode='1100',name='MODE1y'):

    tle = get_MATS_tle()

    configfile = configFile.configFile(
        "data/Operational/configfile_" + mode +"_" + name + ".json",
        DT.datetime.strftime(startdate,"%Y/%m/%d %H:%M:%S"),
        TLE1=tle[0],
        TLE2=tle[1],
    )
    configfile.Timeline_settings()["duration"]["hours"] = duration
    configfile.set_duration()
    configfile.output_dir = "data/Operational_dump/"
    configfile.CheckConfigFile()    
    configfile.Timeline_gen()
    configfile.XML_gen()

    return

def generate_star_staring_mode(startdate,duration,mode='3040',name='STAR'):

    tle = get_MATS_tle()

    configfile = configFile.configFile(
        "data/Operational/configfile_" + mode + "_" + name + ".json",
        DT.datetime.strftime(startdate,"%Y/%m/%d %H:%M:%S"),
        TLE1=tle[0],
        TLE2=tle[1],
    )
    configfile.Timeline_settings()["duration"]["hours"] = duration
    configfile.Mode120_settings()['TimeToConsider']['hours'] = duration
    configfile.Mode120_settings()['TimeToConsider']['TimeToConsider'] = duration*3600
    configfile.set_duration()
    configfile.output_dir = "data/Operational_dump/"
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
