# NCCUCourse

A set of NCCU Course tools, base on python3

## Environment

- Python 3.9^

## Installation

```sh
pip3 install -r requirement.txt
```

## Setup

### Account

As a NCCU student, you have your iNCCU account. Please create a `.env` file and give following informations.

```env
USERNAME=*********
PASSWORD=*****

YEAR=111
SEM=2

GOOGLE_APPLICATION_CREDENTIALS=.google.auth
OPENSSL_CONF=openssl.conf
```

If your google credential is store else where, please modify `.env` file.
Be aware of your credential when using git!!

### unit

You will need to download the unit file from [https://qrysub.nccu.edu.tw/assets/api/unit.json](https://qrysub.nccu.edu.tw/assets/api/unit.json) and save it as `unit.json` in the root directory.

## Execution

```sh
python main.py
```

If you encounter in ssl error, please use `openssl.conf` as your connection configuration file.
Yout entry point will be

```sh
OPENSSL_CONF=openssl.conf python main.py
```
