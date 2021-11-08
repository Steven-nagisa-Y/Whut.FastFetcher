from fastapi import FastAPI
from pydantic import BaseModel
from requests.sessions import Session
import uvicorn
import requests
import json
from model.apires import BadRes, GoodRes
from lib.cwsf_ele import Cwsf
from lib import zhlgd

app = FastAPI()


@app.get("/")
def ping():
    return "pong"


def login2cwsf(cur_session: Session, username: str, password: str) -> bool:
    jsessionid, lt = zhlgd.cas_login(cur_session)
    text = zhlgd.post_cas_login(username, password, jsessionid, lt, cur_session)
    return text != None


class EleFeeFormMa(BaseModel):
    username: str
    password: str
    meter_id: str


# 马区电费查询
@app.post("/cwsf/ele/ma")
def ele_ma(form: EleFeeFormMa):
    cur_session = requests.session()
    if not login2cwsf(cur_session, form.username, form.password):
        return BadRes("查询失败")
    res_json = json.loads(Cwsf(cur_session=cur_session).queryReserve(form.meter_id))
    # 剩余电量
    remain_power: str = (
        "{}{}".format(res_json["remainPower"], res_json["remainName"])
        if (
            res_json.__contains__("remainPower") and res_json.__contains__("remainName")
        )
        else "无数据"
    )
    # 剩余电费
    remain_due: str = (
        res_json["meterOverdue"] if res_json.__contains__("meterOverdue") else "无数据"
    )
    return GoodRes("查询成功", "剩余电量: {}\n剩余电费: {}".format(remain_power, remain_due))


class EleFeeFormYu(BaseModel):
    username: str
    password: str
    roomno: str


# 余区电费查询
@app.post("/cwsf/ele/yu")
def ele_yu(form: EleFeeFormYu):
    cur_session = requests.session()
    if not login2cwsf(cur_session, form.username, form.password):
        return BadRes("查询失败")
    res_json: dict[str, str] = json.loads(
        Cwsf(cur_session=cur_session).querySydl(form.roomno)
    )
    if not res_json.__contains__("roomlist"):
        return BadRes("查询失败")
    room_list = res_json["roomlist"]
    remain_power = (
        "剩余{}: {}".format(room_list["remainName"], room_list["remainPower"])
        if room_list.__contains__("remainName")
        and room_list.__contains__("remainPower")
        else "无数据"
    )
    read_time = (
        "查表时间: {}".format(room_list["readTime"])
        if room_list.__contains__("readTime")
        else "无数据"
    )
    return GoodRes("获取成功", "{}\n{}".format(remain_power, read_time))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        debug=True,
        log_level="info",
    )
