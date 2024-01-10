"""
====================
Fetch Course Result
====================
"""
import os
import csv
import json
import requests
from tqdm import tqdm
from constant import COURSERESULT_CSV, COURSERESULT_YEARSEM

# import shutil


def main():
    for sem in COURSERESULT_YEARSEM:
        i = 0
        with open("./data/" + COURSERESULT_CSV(sem), "r", encoding="utf-8") as f:
            row_count = sum(1 for line in f)
        with open("./data/" + COURSERESULT_CSV(sem), "r", encoding="utf-8") as f:
            reader = tqdm(csv.reader(f), total=row_count)
            for row in reader:
                courseid = str(row[0])
                try:
                    res = requests.get(
                        "https://es.nccu.edu.tw/course/zh-TW/:sem="
                        + sem
                        + "%20"
                        + str(courseid)
                        + "%20/",
                        timeout=10,
                    ).json()
                    result = dict(
                        {
                            "yearsem": sem,
                            "time": res[0]["subTime"],
                            "courseId": courseid,
                            "studentLimit": str(row[3]),
                            "studentCount": str(row[4]),
                            "lastEnroll": str(row[5]),
                        }
                    )
                    dataPath = "./result/" + res[0]["teaNam"] + "/" + res[0]["subNam"]
                    if not os.path.exists(dataPath):
                        os.makedirs(dataPath)
                    if not os.path.exists(dataPath + "/courseResult"):
                        os.makedirs(dataPath + "/courseResult")
                    if not os.path.exists(dataPath + "/courseResult/" + sem + ".json"):
                        with open(
                            dataPath + "/courseResult/" + sem + ".json",
                            "w",
                            encoding="utf-8",
                        ) as file:
                            json.dump([], file)

                    with open(
                        dataPath + "/courseResult/" + sem + ".json",
                        "r",
                        encoding="utf-8",
                    ) as file:
                        originalData = json.loads(file.read())
                    originalData.append(result)
                    with open(
                        dataPath + "/courseResult/" + sem + ".json",
                        "w",
                        encoding="utf-8",
                    ) as file:
                        json.dump(originalData, file)
                except BaseException as err:
                    print(courseid + ": ", err)
                i += 1


if __name__ == "__main__":
    main()
