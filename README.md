# 千代田区バリアフリートイレデータ

東京都千代田区のバリアフリートイレの情報を提供する JSON データセットです。区内のトイレ施設のアクセシビリティ情報や設備情報を含んでいます。

## データについて

このリポジトリには千代田区内のバリアフリートイレに関する以下の情報が含まれています：

- 施設情報（施設名、住所、建物名など）
- 位置情報（緯度・経度）
- バリアフリー設備情報（車椅子対応、オストメイト設備、ベビーチェアなど）
- 利用可能時間
- その他特記事項

## ディレクトリ構造

```
.
├── json/              # 元のJSONデータ
│   └── toilet_data.json  # 千代田区バリアフリートイレデータ（インデント付き）
├── json_min/          # 圧縮されたJSONデータ
│   └── toilet_data.json  # インデントのない形式に変換されたデータ
├── toilet_data_converter.py  # CSVからJSONへの変換スクリプト
└── compact_json.py    # JSONをコンパクト形式に変換するスクリプト
```

## 使用しているツール

### 1. CSV から JSON への変換ツール（toilet_data_converter.py）

千代田区のバリアフリートイレの CSV データを JSON 形式に変換するスクリプトです。

主な機能：

- 列名の英語への変換
- ○× などの値の真偽値(true/false)への変換
- 日付データの ISO 8601 形式への正規化
- 営業時間の「start」と「end」への分割

使用方法：

```bash
python toilet_data_converter.py input.csv output.json
```

### 2. JSON 圧縮ツール（compact_json.py）

JSON ファイルをインデントのないコンパクトな形式に変換するスクリプトです。

主な機能：

- JSON ファイルのインデントを削除してコンパクトな形式に変換
- 単一ファイルまたはディレクトリ内の全 JSON ファイルを一括処理
- 処理したファイルは自動的に`json_min`ディレクトリに保存

使用方法：

```bash
# 単一ファイルの処理
python compact_json.py json/toilet_data.json

# ディレクトリ内の全JSONファイルを処理
python compact_json.py json

# 出力先ディレクトリの指定
python compact_json.py json -o output_directory
```

## データの構造

各トイレのデータは以下のような構造になっています：

```json
{
  "id": "施設ID-トイレID",
  "facility_id": "施設ID",
  "manager_type_id": "管理者種別番号",
  "facility_name": "施設名",
  "prefecture": "都道府県",
  "address": "市区町村・番地",
  "building_name": "ビル建物名",
  "toilet_name": "トイレ名",
  "floor": "設置フロア",
  "gender_type": "性別の分け",
  "location": {
    "longitude": "経度",
    "latitude": "緯度",
    "coordinate_system": "座標系"
  },
  "features": {
    "has_braille_blocks": "点字ブロックの有無",
    "has_voice_guidance": "音声案内の有無",
    "is_wheelchair_accessible": "車椅子対応の有無",
    "has_ostomate_facilities": "オストメイト設備の有無",
    "has_diaper_changing_table": "おむつ交換台の有無"
    // その他の設備情報
  },
  "opening_hours": [
    // 曜日ごとの営業時間情報
  ]
}
```

## ライセンス

このデータセットは、東京都のオープンデータとして公開されています。

[車椅子使用者対応トイレのバリアフリー情報（令和５年度更新版） - CC BY](https://catalog.data.metro.tokyo.lg.jp/dataset/t000054d0000000342)

© 東京都福祉局
