from mats_planningtool.XMLGenerator import XML_gen
import datetime as DT

def test_early_split():
    splitdate = DT.datetime(2002,11,4,20,00,00)
    try:
        XML_gen.XML_splitter('test_data/output/tmp.xml',[splitdate])
    except ValueError:
        pass

# splitdate = DT.datetime(2022,11,4,20,00,00)
# XML_gen.XML_splitter('test_data/output/tmp.xml',[splitdate])

XML_gen.XML_filter('test_data/output/tmp.xml','TC_acfLimbPointingAltitudeOffset')
