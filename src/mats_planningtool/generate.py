import argparse
from mats_planningtool import configFile as configFile


def main(args):
    configfile_original = configFile.configFile(args.configfile)

    # "Check the currently chosen Configuration File and the plausibility of its values. Prints out the currently used start date and TLE"
    configfile_original.CheckConfigFile()

    if args.xmlfile is not None:
        configfile_original.PLUTOGenerator(max_wait_time=60)

    # "Create a Science Mode Timeline (.json file) depending on the settings in the Configuration File"
    elif args.timelinefile is not None:
        print("test")
        XML_TIMELINE = configfile_original.XML_gen(SCIMOD_Path=args.timelinefile)
        configfile_original.PLUTOGenerator(XML_Path=XML_TIMELINE, max_wait_time=60)

    else:
        configfile_original.Timeline_gen()
        configfile_original.XML_gen()
        configfile_original.PLUTOGenerator(max_wait_time=60)

    # "Convert the Science Mode Timeline into payload and platform CMDs as a .xml file)"

    return


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser()

    parser.add_argument("-V", "--version",
                        help="show program version", action="store_true")
    parser.add_argument("configfile",
                        help="input config file")
    parser.add_argument("-t", "--timelinefile",
                        help="input timelinefile")
    parser.add_argument("-x", "--xmlfile",
                        help="input xmlfile")

    return parser.parse_args(argv)


if __name__ == '__main__':
    arguments = parse_arguments()
    main(arguments)
