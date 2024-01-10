"""
==============================
main.py
==============================
"""
# pylint: disable=invalid-name, consider-using-f-string, line-too-long
import sys
import os
import getopt
import logging

from DB import DB
from main_func import process_class, process_teacher, process_rate, process_results

# from translateRate import translateRate

options = "h"
longOptions = ["help", "skip_class", "skip_teacher", "skip_rate", "skip_class_detail"]
argumentList = sys.argv[1:]
allSemesters = [
    "1011",
    "1012",
    "1021",
    "1022",
    "1031",
    "1032",
    "1041",
    "1042",
    "1051",
    "1052",
    "1061",
    "1062",
    "1071",
    "1072",
    "1081",
    "1082",
    "1091",
    "1092",
    "1101",
    "1102",
    "1111",
    "1112",
    "1121",
    "1122",
]

programOptions = {
    "skip_class": False,
    "skip_class_detail": False,
    "skip_teacher": False,
    "skip_rate": False,
    "skip_result": True,
}

dirPath = os.path.dirname(os.path.realpath(__file__))


if __name__ == "__main__":
    try:
        arguments, values = getopt.getopt(argumentList, options, longOptions)
        for currentArgument, currentValue in arguments:
            if currentArgument in ("-h", "--help"):
                print(
                    """
    Usage: python main.py [OPTIONS]...

    Options:
        --skip_class          Skip fetch class operation.
        --skip_class_detail   Skip fetch class detail operation.
        --skip_teacher        Skip fetch teacher operation.
        --skip_rate           Skip fetch rate operation.
        --skip_result         Skip fetch result operation.
        --help, -h            Display this help and exit.            
"""
                )
                sys.exit()
            elif currentArgument in ("--skip_class"):
                programOptions["skip_class"] = True
            elif currentArgument in ("--skip_class_detail"):
                programOptions["skip_class_detail"] = True
            elif currentArgument in ("--skip_teacher"):
                programOptions["skip_teacher"] = True
            elif currentArgument in ("--skip_rate"):
                programOptions["skip_rate"] = True
            elif currentArgument in ("--skip_result"):
                programOptions["skip_result"] = True
    except getopt.error as err:
        print(str(err))
        sys.exit()

    # Setup logger
    logging.basicConfig(
        filename="log.log",
        format="%(asctime)s [%(levelname)s] %(message)s",
        encoding="utf-8",
    )

    if os.path.exists(os.path.join(dirPath, "_data")):
        os.makedirs(os.path.join(dirPath, "_data"), exist_ok=True)

    db = DB("test.db")

    # ==============================
    # \ 1. Fetch Classes           \
    # ==============================

    if not programOptions["skip_class"]:
        try:
            process_class(db, programOptions, allSemesters)
        except Exception as e:
            logging.error(e)
            print("Error: " + str(e))
    else:
        print("Skipping Fetch Class")

    # ==============================
    # \ 2. Fetch TeacherId         \
    # ==============================

    if not programOptions["skip_teacher"]:
        # Read course list
        try:
            process_teacher(db)
        except Exception as e:
            logging.error(e)
            print("Error: " + str(e))
    else:
        print("Skipping Fetch TeacherId")

    # ==============================
    # \ 3. Fetch Rates and Details \
    # ==============================

    if not programOptions["skip_rate"]:
        try:
            process_rate(db, dirPath, allSemesters)
        except Exception as e:
            logging.error(e)
            print("Error: " + str(e))
    else:
        print("Skipping Fetch Rate")

    # ==============================
    # \ 4. Course Result           \
    # ==============================
    if not programOptions["skip_result"]:
        try:
            process_results(db)
        except Exception as e:
            logging.error(e)
            print("Error: " + str(e))
