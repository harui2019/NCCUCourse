"""
================================================================
User.py
================================================================
"""
from os import getenv
from dotenv import load_dotenv
import requests
from requests import JSONDecodeError
from util import get_login_url, get_addtrack_url, get_deltrack_url, get_track_url

load_dotenv()


class User:
    """iNCCU User"""

    _username: str
    _password: str
    _token: str

    def __init__(self) -> None:
        self._username = getenv("USERNAME") or ""
        self._password = getenv("PASSWORD") or ""
        res = requests.get(get_login_url(self._username, self._password), timeout=10)
        try:
            res_json = res.json()
        except JSONDecodeError as exc:
            raise JSONDecodeError("token error", response=res) from exc
        try:
            self._token = res_json[0]["encstu"]
        except KeyError as exc:
            raise ValueError("token error") from exc

    def add_track(self, course_id: str):
        """Add course to track list"""
        addres = requests.post(get_addtrack_url(self._token, course_id), timeout=10)
        try:
            addres_json = addres.json()
        except JSONDecodeError as exc:
            raise JSONDecodeError("Add fail: " + course_id, response=addres) from exc
        if addres_json[0]["procid"] != "1":
            raise ValueError("Add fail: " + course_id)

    def delete_track(self, course_id: str):
        """Delete course from track list"""
        deleteres = requests.delete(
            get_deltrack_url(self._token, course_id), timeout=10
        )
        try:
            deleteres_json = deleteres.json()
        except JSONDecodeError as exc:
            raise JSONDecodeError(
                "Delete fail: " + course_id, response=deleteres
            ) from exc
        if deleteres_json[0]["procid"] != "9":
            raise ValueError("Delete fail: " + course_id)

    def get_track(self):
        """Get track list

        Returns:
            dict: track list
        """
        courseres = requests.get(get_track_url(self._token), timeout=10)
        try:
            courseres_json = courseres.json()
        except JSONDecodeError as exc:
            raise JSONDecodeError("Get fail", response=courseres) from exc
        return courseres_json
