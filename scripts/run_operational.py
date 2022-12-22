from mats_planningtool import configFile as configFile
import datetime as DT
import requests as R

def get_MATS_tle():
    query = 'https://celestrak.org/NORAD/elements/gp.php?CATNR=54227&FORMAT=tle'
    celestrak = R.session()
    tle = celestrak.get(query).text.split('\r\n')[1:3]
    print('using Mats tle \n',tle)
    return tle

def generate_operational_mode(startdate,duration):
    configfile = configFile.configFile(
        "data/Operational/configfile_1100_MODE1y.json",
        DT.datetime.strftime(startdate,"%Y/%m/%d %H:%M:%S"),
        TLE1=tle[0],
        TLE2=tle[1],
    )
    configfile.Timeline_settings()["duration"]["hours"] = duration
    configfile.set_duration()
    configfile.output_dir = "data/Operational/"
    configfile.CheckConfigFile()    
    configfile.Timeline_gen()
    configfile.XML_gen()

    return


tle = get_MATS_tle()


# generate_operational_mode(DT.datetime(2022,12,21,18,00),6)
# generate_operational_mode(DT.datetime(2022,12,22,18,00),9)
# generate_operational_mode(DT.datetime(2022,12,23,18,00),9)
# generate_operational_mode(DT.datetime(2022,12,24,18,00),9)
# generate_operational_mode(DT.datetime(2022,12,25,18,00),9)
# generate_operational_mode(DT.datetime(2022,12,26,18,00),9)
# generate_operational_mode(DT.datetime(2022,12,27,18,00),9)
generate_operational_mode(DT.datetime(2022,12,28,18,00),9)
generate_operational_mode(DT.datetime(2022,12,29,18,00),9)