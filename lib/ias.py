import json
import re
from typing import Tuple
from urllib.parse import urlencode

import requests
from lxml import etree
from requests import Response

from lib.js_reader import des3


class Ias:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.session()

    def login(self) -> bool:
        res = self.session.get("http://zhlgd.whut.edu.cn/tpass/login")
        lt = etree.HTML(res.text).xpath("//input[@id='lt']/@value")[0]
        res = self.session.post(
            "http://zhlgd.whut.edu.cn/tpass/login?service=http%3A%2F%2Fzhlgd.whut.edu.cn%2Ftp_up%2F",
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
            data=urlencode({
                "rsa": des3(self.username, self.password, lt),
                "ul": len(self.username),
                "pl": len(self.password),
                "lt": lt,
                "execution": "e1s1",
                "_eventId": "submit",
            }))

        return res.url.startswith("http://zhlgd.whut.edu.cn/tp_up/view")

    def get_room_code(self, query: str, factory_code: str = "E035") -> Tuple[bool, str]:
        self.factory_code = factory_code
        haihong = open("./model/room-haihong.json",
                       "r", encoding="utf-8").read()
        haihong = json.loads(haihong)
        matches = re.match(r"海虹(?P<build>\d)栋-?(?P<room>\d{3})", query, re.I)
        if not matches:
            return (False, "寝室查询错误")
        build = matches.groupdict()['build']
        room = matches.groupdict()['room']
        if build not in ["5"]:
            return (False, "暂不支持")
        roomid = ""
        for roomIds in haihong[build]['roomlist']:
            if roomIds.endswith(room):
                roomid = roomIds[:8]
                break
        if roomid == "":
            return (False, "寝室号不存在")
        self.session.get("http://cwsf.whut.edu.cn/casLogin")
        res = self.session.post(
            "http://cwsf.whut.edu.cn/queryRoomElec",
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": "http://cwsf.whut.edu.cn",
                "Referer": "http://cwsf.whut.edu.cn/yjtPayElecPages51297E035"
            },
            data=urlencode({
                "roomid": roomid,
                "factorycode": self.factory_code
            })
        )
        res = res.json()
        if "meterId" in res:
            return (True, res['meterId'])
        else:
            return (False, "请求错误")

    def fetch_electric_fee(self, meter_id: str) -> Response:
        self.session.get("http://cwsf.whut.edu.cn/casLogin")
        return self.session.post(
            "http://cwsf.whut.edu.cn/queryReserve",
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
            data=urlencode({
                "meterId": meter_id,
                "factorycode": self.factory_code
            })
        )

    def fetch_books(self) -> Response:
        url = "http://zhlgd.whut.edu.cn/tp_up/up/sysintegration/getlibraryRecordList"
        # {"draw":1,"order":[],"pageNum":1,"pageSize":10,"start":0,"length":10,"appointTime":"","dateSearch":"","startDate":"","endDate":""}
        data = {
            "draw": 1,
            "order": [],
            "pageNum": 1,
            "pageSize": 50,
            "start": 0,
            "length": 10,
            "appointTime": "",
            "dateSearch": "",
            "startDate": "",
            "endDate": "",
        }
        headers = {"Content-Type": "application/json"}
        return self.session.post(url=url, headers=headers, data=json.dumps(data))
