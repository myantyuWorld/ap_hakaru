# -*- coding: utf-8 -*-
from tinydb import TinyDB, Query

db = TinyDB("analysis.json")

# test method
def insert_test():
    db.insert({"name": "foo", "age": 20})

def select_all():
    return db.all()
    
#
# 解析結果を格納します
#     meter_value : 計測値
#     meter_time : 解析時刻
#     analysis_result : AIの解析結果
#
def insert_analysis(meter_value, meter_time, analysis_result):
    db.insert({
      "meter_value" : meter_value,
      "meter_time" : meter_time,
      "analysis_result" : analysis_result,
    })