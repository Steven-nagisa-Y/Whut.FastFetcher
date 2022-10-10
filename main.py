from fastapi import FastAPI
import uvicorn

from lib.ias import Ias
from model.apires import BadRes, GoodRes
from model.form import *

app = FastAPI()


@app.get("/ping", status_code=200)
@app.get("/")
def ping():
    return "pong"


# 电费查询
@app.post("/electric")
def electric(form: ElectricForm):
    ias = Ias(form.username, form.password)
    if not ias.login():
        return BadRes("登录失败,检查账密是否正确！")
    ok, meterId = ias.get_room_code(form.query, form.factoryCode)
    if not ok:
        return BadRes(meterId)

    res = ias.fetch_electric_fee(meterId)

    res = res.json()

    # 剩余电量
    remain_power: str = (
        "{}{}".format(res["remainPower"], res["remainName"])
        if (
            res.__contains__(
                "remainPower") and res.__contains__("remainName")
        )
        else "无数据"
    )
    # 剩余电费
    remain_due = res.get("meterOverdue", "无数据")
    return GoodRes("查询成功", "剩余电量: {}\n剩余电费: {}".format(remain_power, remain_due))


@app.post("/books")
def books(form: BooksForm):
    ias = Ias(form.username, form.password)
    if not ias.login():
        return BadRes("登录失败,检查账密是否正确！")
    res = ias.fetch_books()
    return GoodRes("图书获取成功", res.json())


if __name__ == "__main__":
    from sys import argv
    if len(argv) > 1 and argv[1].isdigit():
        port = int(argv[1])
    else:
        port = 8000
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=port,
        reload=True,
        debug=True,
        log_level="info",
    )
