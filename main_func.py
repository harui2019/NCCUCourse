"""
==============================
main_func.py
==============================
"""
# pylint: disable=invalid-name, consider-using-f-string, line-too-long, broad-exception-caught
import os
import json
import logging
import csv
import datetime
from time import sleep
import tqdm
from bs4 import BeautifulSoup
import requests

from DB import DB
from User import User
from constant import YEAR_SEM, YEAR, SEM, COURSERESULT_CSV, COURSERESULT_YEARSEM
from fetchDescription import fetch_description
from fetchRate import fetch_rate


def process_class(
    db: DB,
    programOptions: dict[str, bool],
    allSemesters: list[str],
):
    """Process class data

    Args:
        db (DB): DB instance
        programOptions (dict[str, bool]): program options
        allSemesters (list[str]): all semesters
    """
    # fetch all deps first, make a single search less than 500
    with open("./unit.json", "r", encoding="utf-8") as f:
        units = json.loads(f.read())
        categories = []
        for dp1 in [x for x in units if x["utCodL1"] != "0"]:
            for dp2 in [x for x in dp1["utL2"] if x["utCodL2"] != "0"]:
                for dp3 in [x for x in dp2["utL3"] if x["utCodL3"] != "0"]:
                    categories.append(
                        {
                            "dp1": dp1["utCodL1"],
                            "dp2": dp2["utCodL2"],
                            "dp3": dp3["utCodL3"],
                        }
                    )

    # run through all deps, get their classId
    coursesList = []
    tqdmCategories = tqdm.tqdm(categories, leave=False)
    for category in tqdmCategories:
        tqdmCategories.set_postfix_str("{}".format(category))
        if not programOptions["skip_class_detail"]:
            semesters = tqdm.tqdm(allSemesters, leave=False)
        else:
            semesters = ["1121"]
        for semester in semesters:
            if not programOptions["skip_class_detail"]:
                semesters.set_postfix_str("processing: {}".format(semester))
            try:
                sleep(0.1)
                res = requests.get(
                    "https://es.nccu.edu.tw/course/zh-TW/:sem={} :dp1={} :dp2={} :dp3={}".format(
                        semester, category["dp1"], category["dp2"], category["dp3"]
                    ),
                    timeout=100,
                )
                res.raise_for_status()
                courses = res.json()
                if len(courses) >= 500:
                    raise ValueError("{} too large".format(category))

                # Add to courseList
                if semester == YEAR_SEM:
                    coursesList += [x["subNum"] for x in courses]

                # Write to databse
                for course in tqdm.tqdm(courses, leave=False):
                    courseId = "{}{}".format(semester, course["subNum"])
                    # if db.isCourseExist(courseId, category):
                    #   continue
                    detail = fetch_description(courseId)
                    db.addCourse(
                        detail["qrysub"],
                        detail["qrysubEn"],
                        category["dp1"],
                        category["dp2"],
                        category["dp3"],
                        "".join(detail["description"]),
                        "".join(detail["objectives"]),
                    )
            except Exception as e:
                logging.error(e)

    logging.debug(coursesList)

    print("Fetch Class done at {}".format(datetime.datetime.now()))


def process_teacher(
    db: DB,
):
    """Process teacher data

    Args:
        db (DB): DB instance
    """
    coursesList = db.getThisSemesterCourse(YEAR, SEM)

    user = User()

    # Delete exist track courses before adding
    courses = user.get_track()
    if len(courses) > 0:
        tqdmCourses = tqdm.tqdm(courses, leave=False)
        for course in tqdmCourses:
            try:
                sleep(0.2)
                courseId = str(course["subNum"])
                tqdmCourses.set_postfix_str("Pre-deleting {}".format(courseId))
                user.delete_track(courseId)
            except Exception as e:
                logging.error(e)
                continue

    # Add courses to track list
    tqdmCourses = tqdm.tqdm([*set(coursesList)], leave=False)
    for courseId in tqdmCourses:
        try:
            sleep(0.2)
            tqdmCourses.set_postfix_str("Adding {}".format(courseId))
            user.add_track(courseId)
        except Exception as e:
            logging.error(e)
            continue

    # get track list and parse out teacher id
    courses = user.get_track()
    teacherIdDict = {}
    tqdmCourses = tqdm.tqdm(courses, leave=False)
    for course in tqdmCourses:
        try:
            teacherStatUrl = str(course["teaStatUrl"])
            teacherName = str(course["teaNam"])
            tqdmCourses.set_postfix_str("Processing {}".format(teacherName))
            if teacherStatUrl.startswith(
                "https://newdoc.nccu.edu.tw/teaschm/{}/statisticAll.jsp".format(
                    YEAR_SEM
                )
            ):
                teacherId = teacherStatUrl.split(
                    "https://newdoc.nccu.edu.tw/teaschm/{}/statisticAll.jsp-tnum=".format(
                        YEAR_SEM
                    )
                )[1].split(".htm")[0]
                teacherIdDict[teacherName] = teacherId
                db.addTeacher(teacherId, teacherName)
            elif teacherStatUrl.startswith(
                "https://newdoc.nccu.edu.tw/teaschm/{}/set20.jsp".format(YEAR_SEM)
            ):
                # use ip to avoid name resolve error, and add time out
                res = requests.get(
                    teacherStatUrl.replace(
                        "newdoc.nccu.edu.tw", "140.119.229.20"
                    ).replace("https://", "http://"),
                    timeout=10,
                )
                res.raise_for_status()
                sleep(0.2)
                soup = BeautifulSoup(
                    res.content.decode("big5").encode("utf-8"), "html.parser"
                )
                rows = soup.find_all("tr")
                for row in [
                    x.find_all("td")
                    for x in soup.find_all("tr")
                    if x.find_all("td")[1].find("a")
                ]:
                    teacherName = str(row[0].text)
                    teacherId = (
                        row[-1]
                        .find("a")["href"]
                        .split("statisticAll.jsp-tnum=")[1]
                        .split(".htm")[0]
                    )
                    teacherIdDict[teacherName] = teacherId
                    db.addTeacher(teacherId, teacherName)
        except Exception as e:
            logging.error(e)
            continue

    # Delete courses from track list
    tqdmCourses = tqdm.tqdm(courses, leave=False)
    for course in tqdmCourses:
        try:
            sleep(0.2)
            courseId = str(course["subNum"])
            tqdmCourses.set_postfix_str("Deleting {}".format(courseId))
            user.delete_track(courseId)
        except Exception as e:
            logging.error(e)
            continue

    print("Fetch TeacherId done at {}".format(datetime.datetime.now()))


def process_rate(
    db: DB,
    dirPath: str,
    allSemesters: list[str],
):
    """Process rate data

    Args:
        db (DB): DB instance
        dirPath (str): directory path
        allSemesters (list[str]): all semesters
    """
    # Read teacher list
    newTeacherList = db.getTeachers()
    with open(
        os.path.join(dirPath, "old_data", "1111_teachers.json"),
        "r",
        encoding="utf8",
    ) as f:
        oldTeacherList = json.loads(f.read())
    teacherList = {**newTeacherList, **oldTeacherList}
    with open(
        os.path.join(dirPath, "old_data", "1112_teachers.json"),
        "r",
        encoding="utf8",
    ) as f:
        oldTeacherList = json.loads(f.read())
    teacherList = {**newTeacherList, **oldTeacherList}

    # Run through all teacherId, and fetch courses of teachers
    teachers = tqdm.tqdm(teacherList, total=len(teacherList), leave=False)
    for teacher in teachers:
        teacherId = teacherList[teacher]
        teachers.set_postfix_str("processing: {} {}".format(teacherId, teacher))
        semesters = tqdm.tqdm(allSemesters, total=len(allSemesters), leave=False)
        for semester in semesters:
            semesters.set_postfix_str("processing: {}".format(semester))
            try:
                location = "http://newdoc.nccu.edu.tw/teaschm/{}/statistic.jsp-tnum={}.htm".format(
                    semester, teacherId
                )
                res = requests.get(location, timeout=10)
                res.raise_for_status()
                soup = BeautifulSoup(
                    res.content.decode("big5").encode("utf-8"), "html.parser"
                )
                courses = soup.find("table", {"border": "1"}).find_all("tr")
                availableCourses = [
                    x.find_all("td")
                    for x in courses
                    if x.find_all("td")[-1].find("a")
                    and int(x.find_all("td")[0].text) > 100
                ]
                tqdmCourses = tqdm.tqdm(
                    availableCourses, total=len(availableCourses), leave=False
                )

                for row in tqdmCourses:
                    courseId = "{}{}{}".format(row[0].text, row[1].text, row[2].text)
                    tqdmCourses.set_postfix_str("processing: {}".format(courseId))
                    if db.isRateExist(courseId):
                        continue
                    sleep(0.2)
                    rates = fetch_rate(
                        "http://newdoc.nccu.edu.tw/teaschm/{}/{}".format(
                            semester, row[-1].find("a")["href"]
                        )
                    )

                    # Write to database
                    tqdmRates = tqdm.tqdm(rates, total=len(rates), leave=False)
                    for index, rate in enumerate(tqdmRates):
                        # rateEn = translateRate(str(rate))
                        rateEn = ""
                        db.addRate(index, courseId, teacherId, str(rate), rateEn)

            except Exception as e:
                logging.error(e)
                continue

    print("Fetch Rates and Details done at {}".format(datetime.datetime.now()))


def process_results(
    db: DB,
):
    """Process course result data

    Args:
        db (DB): DB instance
    """
    for sem in COURSERESULT_YEARSEM:
        with open("./data/" + COURSERESULT_CSV(sem), "r", encoding="utf-8") as f:
            row_count = sum(1 for line in f)
        with open("./data/" + COURSERESULT_CSV(sem), "r", encoding="utf-8") as f:
            lines = list(f)
            i = 0
            reader = tqdm.tqdm(csv.reader(lines), total=len(lines))
            for row in reader:
                courseid = str(row[0])
                try:
                    sleep(0.2)
                    res = requests.get(
                        "https://es.nccu.edu.tw/course/zh-TW/:sem="
                        + sem
                        + "%20"
                        + str(courseid)
                        + "%20/",
                        timeout=100,
                    ).json()
                    db.addResult(
                        sem,
                        courseid,
                        res[0]["subNam"],
                        res[0]["teaNam"],
                        res[0]["subTime"],
                        int(row[3]),
                        int(row[4]),
                        -1 if row[5] == "" else int(row[5]),
                    )
                except Exception as err:
                    logging.error(err)
                    continue
                i += 1
