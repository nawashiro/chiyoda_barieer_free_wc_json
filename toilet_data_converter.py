#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
バリアフリートイレデータ変換スクリプト

このスクリプトは、千代田区のバリアフリートイレのCSVデータをJSON形式に変換します。
CSVの列名は英語に変換され、○×などの値は真偽値(true/false)に変換されます。
NaN値はnullに変換されます。
営業時間は「start」と「end」に分けられます。
日付データはISO 8601形式（YYYY-MM）に正規化されます。
削除された施設（deleted_dateに値があるデータ）は出力から除外されます。
各トイレは独立したレコードとして出力され、階層構造化されません。

使用方法:
    python toilet_data_converter.py input.csv output.json

引数:
    input_csv: 入力CSVファイルのパス
    output_json: 出力JSONファイルのパス

仮想環境:
    このスクリプトは既存のvenv環境を使用します。
    必要なパッケージ: pandas
"""

import argparse
import json
import os
import pandas as pd
import re
import sys
from json import JSONEncoder


# NaN値をNoneに変換するためのJSONEncoderを拡張
class NpEncoder(JSONEncoder):
    def default(self, obj):
        if pd.isna(obj):
            return None
        return super(NpEncoder, self).default(obj)


def convert_to_boolean(value):
    """
    ○×などの値を真偽値に変換する関数
    
    Args:
        value: 変換する値
        
    Returns:
        bool: 変換後の真偽値、またはNaNの場合はNone
    """
    if pd.isna(value):
        return None
    
    # ○やマルに類似する文字を真と見なす
    if isinstance(value, str) and (value == '○' or value == '◯' or value == '丸' or value == 'マル'):
        return True
    # ×やバツに類似する文字を偽と見なす
    elif isinstance(value, str) and (value == '×' or value == '✕' or value == '☓' or value == 'バツ'):
        return False
    # 「有」は真、「無」は偽と見なす
    elif isinstance(value, str) and value == '有':
        return True
    elif isinstance(value, str) and value == '無':
        return False
    # それ以外は元の値を返す
    return value


def format_date(date_value):
    """
    日付値を ISO 8601 形式 (YYYY-MM) に整形する関数
    
    Args:
        date_value: 整形する日付値（202401.0 のような形式）
        
    Returns:
        str: ISO 8601形式の日付（例: "2024-01"）、またはNaNの場合はNone
    """
    if pd.isna(date_value):
        return None
    
    # 数値の場合、文字列に変換して小数点以下を削除
    if isinstance(date_value, (int, float)):
        date_str = str(int(date_value))
    # 文字列で「.0」が含まれている場合、それを削除
    elif isinstance(date_value, str) and '.0' in date_value:
        date_str = date_value.replace('.0', '')
    else:
        date_str = str(date_value)
    
    # 日付形式を検出（YYYYMM）
    if re.match(r'^\d{6}$', date_str):
        year = date_str[:4]
        month = date_str[4:6]
        return f"{year}-{month}"
    
    # 日付形式を検出（YYYYMMDD）
    if re.match(r'^\d{8}$', date_str):
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        return f"{year}-{month}-{day}"
    
    # 元々ISO形式の場合はそのまま返す
    if re.match(r'^\d{4}-\d{2}(-\d{2})?$', date_str):
        return date_str
    
    # その他の形式の場合は元の値を返す
    return date_str


def parse_hours(time_string):
    """
    時間文字列を解析して開始時間と終了時間に分割する
    
    Args:
        time_string: 解析する時間文字列（例: '0800_1645'）
        
    Returns:
        dict: 開始時間と終了時間を含む辞書、または時間形式でない場合は元の値
    """
    if pd.isna(time_string) or not isinstance(time_string, str):
        return {"start": None, "end": None}
    
    # 「0800_1645」のような形式を検出
    pattern1 = r'(\d{4})_(\d{4})'
    match1 = re.search(pattern1, time_string)
    if match1:
        start_raw = match1.group(1)
        end_raw = match1.group(2)
        
        # HHMMをHH:MMの形式に変換
        start_time = f"{start_raw[:2]}:{start_raw[2:]}" if len(start_raw) == 4 else start_raw
        end_time = f"{end_raw[:2]}:{end_raw[2:]}" if len(end_raw) == 4 else end_raw
        
        return {"start": start_time, "end": end_time}
    
    # 時間範囲のパターンを検出（8:30～19:00、8時30分〜19時00分、など）
    pattern2 = r'(\d{1,2}[:|時]?\d{0,2}分?)\s*[~～〜-]\s*(\d{1,2}[:|時]?\d{0,2}分?)'
    match2 = re.search(pattern2, time_string)
    if match2:
        start_time = match2.group(1)
        end_time = match2.group(2)
        return {"start": start_time, "end": end_time}
    
    # 24時間営業などの特殊ケース
    if '24時間' in time_string or '常時' in time_string:
        return {"start": "00:00", "end": "24:00"}
    
    # 解析できない場合は元の文字列を返す
    return {"note": time_string, "start": None, "end": None}


def create_english_column_mapping():
    """
    日本語の列名を英語に変換するマッピングを作成する関数
    
    Returns:
        dict: 日本語列名から英語列名へのマッピング辞書
    """
    return {
        "管理者種別番号": "manager_type_id",
        "部局番号": "department_id",
        "施設種別番号": "facility_type_id",
        "施設通し番号": "facility_id",
        "施設内トイレ通し番号": "toilet_id",
        "施設名": "facility_name",
        "都道府県": "prefecture",
        "市区町村・番地": "address",
        "ビル建物名": "building_name",
        "トイレ名": "toilet_name",
        "設置フロア": "floor",
        "経度": "longitude",
        "緯度": "latitude",
        "座標系": "coordinate_system",
        "性別の分け": "gender_type",
        "トイレへの誘導路として点字ブロックを敷設している": "has_braille_blocks",
        "トイレの位置等を音声で案内している": "has_voice_guidance",
        "戸の形式": "door_type",
        "車椅子が出入りできる（出入口の有効幅員80cm以上）": "is_wheelchair_accessible",
        "車椅子が転回できる（直径150cm以上の円が内接できる）": "has_wheelchair_turning_space",
        "便座に背もたれがある": "has_backrest",
        "便座に手すりがある": "has_handrails",
        "オストメイト用設備がある": "has_ostomate_facilities",
        "オストメイト用設備が温水対応している": "has_warm_water_ostomate",
        "大型ベッドを備えている": "has_large_bed",
        "乳幼児用おむつ交換台等を備えている": "has_diaper_changing_table",
        "乳幼児用椅子を備えている": "has_baby_chair",
        "非常用呼び出しボタンを設置している": "has_emergency_call_button",
        "利用できる時間は、通年変わらない": "has_consistent_hours",
        "月曜日": "monday_hours",
        "火曜日": "tuesday_hours",
        "水曜日": "wednesday_hours",
        "木曜日": "thursday_hours",
        "金曜日": "friday_hours",
        "土曜日": "saturday_hours",
        "日曜日": "sunday_hours",
        "祝日": "holiday_hours",
        "その他": "other_hours_info",
        "季節によって利用可能が異なる場合の期間": "seasonal_period_1",
        "月曜日2": "monday_hours_season2",
        "火曜日2": "tuesday_hours_season2",
        "水曜日2": "wednesday_hours_season2",
        "木曜日2": "thursday_hours_season2",
        "金曜日2": "friday_hours_season2",
        "土曜日2": "saturday_hours_season2",
        "日曜日2": "sunday_hours_season2",
        "祝日2": "holiday_hours_season2",
        "その他2": "other_hours_info_season2",
        "季節によって利用可能が異なる場合の期間.1": "seasonal_period_2",
        "月曜日3": "monday_hours_season3",
        "火曜日3": "tuesday_hours_season3",
        "水曜日3": "wednesday_hours_season3",
        "木曜日3": "thursday_hours_season3",
        "金曜日3": "friday_hours_season3",
        "土曜日3": "saturday_hours_season3",
        "日曜日3": "sunday_hours_season3",
        "祝日3": "holiday_hours_season3",
        "その他3": "other_hours_info_season3",
        "季節によって利用可能が異なる場合の期間.2": "seasonal_period_3",
        "写真データ（トイレの入り口）": "photo_entrance",
        "写真データ（トイレ内）": "photo_inside",
        "写真データ（トイレ内（別角度））": "photo_inside_alt",
        "備考": "notes",
        "データの作成年月": "created_date",
        "データの変更年月": "updated_date",
        "データの削除年月": "deleted_date"
    }


def create_flat_structure(data):
    """
    JSONデータをフラットな構造に整理する関数
    
    Args:
        data: 処理前のJSONデータリスト
        
    Returns:
        list: フラット化されたJSONデータリスト
    """
    flattened_data = []
    
    for item in data:
        # 施設の共通ID部分
        facility_key = f"{item['manager_type_id']}-{item['department_id']}-{item['facility_type_id']}-{item['facility_id']}"
        
        # 営業時間を整理
        opening_hours = []
        weekdays = [
            {"day": "monday", "name": "月曜日"},
            {"day": "tuesday", "name": "火曜日"},
            {"day": "wednesday", "name": "水曜日"},
            {"day": "thursday", "name": "木曜日"},
            {"day": "friday", "name": "金曜日"},
            {"day": "saturday", "name": "土曜日"},
            {"day": "sunday", "name": "日曜日"},
            {"day": "holiday", "name": "祝日"}
        ]
        
        # 通常営業時間
        for weekday in weekdays:
            key = f"{weekday['day']}_hours"
            if key in item and item[key] is not None:
                hours_data = {
                    "day": weekday["day"],
                    "day_name": weekday["name"],
                    "season": 1,
                    "hours": item[key]
                }
                opening_hours.append(hours_data)
        
        # シーズン2の営業時間
        if item.get("seasonal_period_1"):
            for weekday in weekdays:
                key = f"{weekday['day']}_hours_season2"
                if key in item and item[key] is not None:
                    hours_data = {
                        "day": weekday["day"],
                        "day_name": weekday["name"],
                        "season": 2,
                        "season_description": item.get("seasonal_period_1"),
                        "hours": item[key]
                    }
                    opening_hours.append(hours_data)
        
        # シーズン3の営業時間
        if item.get("seasonal_period_2"):
            for weekday in weekdays:
                key = f"{weekday['day']}_hours_season3"
                if key in item and item[key] is not None:
                    hours_data = {
                        "day": weekday["day"],
                        "day_name": weekday["name"],
                        "season": 3,
                        "season_description": item.get("seasonal_period_2"),
                        "hours": item[key]
                    }
                    opening_hours.append(hours_data)
        
        # バリアフリー機能を整理
        barrier_free_features = {
            "has_braille_blocks": item.get("has_braille_blocks"),
            "has_voice_guidance": item.get("has_voice_guidance"),
            "is_wheelchair_accessible": item.get("is_wheelchair_accessible"),
            "has_wheelchair_turning_space": item.get("has_wheelchair_turning_space"),
            "has_backrest": item.get("has_backrest"),
            "has_handrails": item.get("has_handrails"),
            "has_ostomate_facilities": item.get("has_ostomate_facilities"),
            "has_warm_water_ostomate": item.get("has_warm_water_ostomate"),
            "has_large_bed": item.get("has_large_bed"),
            "has_diaper_changing_table": item.get("has_diaper_changing_table"),
            "has_baby_chair": item.get("has_baby_chair"),
            "has_emergency_call_button": item.get("has_emergency_call_button")
        }
        
        # トイレごとの位置情報
        location = {
            "longitude": item["longitude"],
            "latitude": item["latitude"],
            "coordinate_system": item["coordinate_system"]
        }
        
        # 新しいIDを作成（各要素をハイフンで連結）
        toilet_id = f"{facility_key}-{item['toilet_id']}"
        
        # トイレ情報を作成（施設情報を含む）
        toilet = {
            "id": toilet_id,
            "facility_id": facility_key,
            "manager_type_id": item["manager_type_id"],
            "department_id": item["department_id"],
            "facility_type_id": item["facility_type_id"],
            "facility_seq_id": item["facility_id"],
            "toilet_seq_id": item["toilet_id"],
            "facility_name": item["facility_name"],
            "prefecture": item["prefecture"],
            "address": item["address"],
            "building_name": item["building_name"],
            "toilet_name": item["toilet_name"],
            "floor": item["floor"],
            "gender_type": item["gender_type"],
            "door_type": item["door_type"],
            "location": location,
            "features": barrier_free_features,
            "opening_hours": opening_hours,
            "has_consistent_hours": item.get("has_consistent_hours"),
            "other_hours_info": item.get("other_hours_info"),
            "notes": item.get("notes"),
            "photos": {
                "entrance": item.get("photo_entrance"),
                "inside": item.get("photo_inside"),
                "inside_alt": item.get("photo_inside_alt")
            },
            "metadata": {
                "created_date": item.get("created_date"),
                "updated_date": item.get("updated_date")
            }
        }
        
        flattened_data.append(toilet)
    
    # ID順にソート
    flattened_data.sort(key=lambda x: x["id"])
    
    return flattened_data


def convert_csv_to_json(input_csv, output_json):
    """
    CSVファイルをJSONに変換する関数
    
    Args:
        input_csv: 入力CSVファイルのパス
        output_json: 出力JSONファイルのパス
    """
    # CSVファイルを読み込む
    try:
        df = pd.read_csv(input_csv, encoding='utf-8')
    except UnicodeDecodeError:
        # UTF-8でデコードできない場合はShift-JISで試行
        df = pd.read_csv(input_csv, encoding='shift-jis')
    
    # 列名を表示（デバッグ用）
    print("CSVの列名:")
    for col in df.columns:
        print(f"  - {col}")
    
    # 列名の英語化マッピングを取得
    column_mapping = create_english_column_mapping()
    
    # DataFrameの列名を英語に変換
    df.rename(columns=column_mapping, inplace=True)
    
    # 変換後の列名を表示（デバッグ用）
    print("変換後の列名:")
    for col in df.columns:
        print(f"  - {col}")
    
    # 真偽値に変換すべき列のリスト
    boolean_columns = [
        "has_braille_blocks", "has_voice_guidance", "is_wheelchair_accessible",
        "has_wheelchair_turning_space", "has_backrest", "has_handrails", 
        "has_ostomate_facilities", "has_warm_water_ostomate", "has_large_bed",
        "has_diaper_changing_table", "has_baby_chair", "has_emergency_call_button",
        "has_consistent_hours"
    ]
    
    # 日付形式に変換すべき列のリスト
    date_columns = [
        "created_date", "updated_date", "deleted_date"
    ]
    
    # 各列の値を変換
    for col in boolean_columns:
        if col in df.columns:
            df[col] = df[col].apply(convert_to_boolean)
    
    # 日付列の処理
    for col in date_columns:
        if col in df.columns:
            df[col] = df[col].apply(format_date)
    
    # 時間に関する列のリスト
    hours_columns = [
        "monday_hours", "tuesday_hours", "wednesday_hours", "thursday_hours",
        "friday_hours", "saturday_hours", "sunday_hours", "holiday_hours",
        "monday_hours_season2", "tuesday_hours_season2", "wednesday_hours_season2", "thursday_hours_season2",
        "friday_hours_season2", "saturday_hours_season2", "sunday_hours_season2", "holiday_hours_season2",
        "monday_hours_season3", "tuesday_hours_season3", "wednesday_hours_season3", "thursday_hours_season3",
        "friday_hours_season3", "saturday_hours_season3", "sunday_hours_season3", "holiday_hours_season3"
    ]
    
    # すべての列のNaN値をNoneに変換
    df = df.where(pd.notna(df), None)
    
    # 削除されたデータ（deleted_dateに値があるデータ）を除外
    if "deleted_date" in df.columns:
        original_count = len(df)
        df = df[df["deleted_date"].isna()]
        excluded_count = original_count - len(df)
        if excluded_count > 0:
            print(f"削除されたデータ {excluded_count} 件を除外しました。")
    
    # DataFrameをJSON形式に変換
    json_data = df.to_dict(orient='records')
    
    # 各レコードを処理してNaN値をNoneに変換する
    processed_data = []
    for record in json_data:
        # 各フィールドをチェックし、NaNをNoneに変換
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            # 営業時間を開始時間と終了時間に分割
            elif key in hours_columns and value is not None:
                hours_info = parse_hours(value)
                record[key] = hours_info
            
        processed_data.append(record)
    
    # データ構造をフラット化
    flattened_data = create_flat_structure(processed_data)
    
    # JSONファイルに保存（カスタムエンコーダーを使用）
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(flattened_data, f, ensure_ascii=False, indent=2, cls=NpEncoder)
    
    print(f"変換完了: {input_csv} → {output_json}")
    print(f"トイレデータ: 合計 {len(flattened_data)} 件のトイレ情報を変換しました。")


def main():
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='バリアフリートイレのCSVデータをJSONに変換するスクリプト')
    parser.add_argument('input_csv', help='入力CSVファイルのパス')
    parser.add_argument('output_json', help='出力JSONファイルのパス')
    args = parser.parse_args()
    
    # 入力ファイルの存在チェック
    if not os.path.exists(args.input_csv):
        print(f"エラー: 入力ファイル '{args.input_csv}' が見つかりません。", file=sys.stderr)
        return 1
    
    # 変換処理の実行
    try:
        convert_csv_to_json(args.input_csv, args.output_json)
        return 0
    except Exception as e:
        print(f"エラー: 変換処理中に例外が発生しました: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 