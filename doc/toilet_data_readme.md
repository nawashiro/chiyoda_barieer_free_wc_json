# バリアフリートイレデータ変換ツール

このツールは、千代田区のバリアフリートイレの CSV データを JSON 形式に変換するスクリプトです。csv は事前にフィルタしておく必要があります。

## 機能

- CSV データの列名を日本語から英語に変換
- ○× などの記号を真偽値（true/false）に変換
- NaN 値を null（JSON 形式では`null`）に変換
- 営業時間の文字列を開始時間（start）と終了時間（end）に分割
- 日付データを ISO 8601 形式（YYYY-MM または YYYY-MM-DD）に正規化
- 削除された施設（deleted_date に値があるデータ）を出力から除外
- 各トイレを独立したレコードとしてフラット構造で出力
- トイレごとに一意の ID を付与（施設情報とトイレ番号を組み合わせた形式）
- 結果を JSON 形式で出力

## 必要環境

- Python 3.7 以上
- pandas

## インストール

venv を有効化します。

```bash
# Windows
.\.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

必要なパッケージが不足している場合は、以下のコマンドでインストールしてください：

```bash
pip install pandas
```

## 使い方

コマンドラインから以下のように実行します：

```bash
python toilet_data_converter.py <入力CSVファイル> <出力JSONファイル>
```

### 例

```bash
python toilet_data_converter.py .temp/toilet/3_koukyoshisetsu_barieer_free_wc.csv json/toilet_data.json
```

## 入力データの形式

入力する CSV ファイルは以下のような形式である必要があります：

- 列名に日本語を使用（例：「施設名」「トイレ名」）
- 真偽値として「○」「×」などの記号を使用
- 営業時間は「0800_1645」のような形式
- 日付データは「202401.0」のような数値形式の場合があります
- deleted_date に値がある場合は削除済みデータとして扱われます

## フラット構造の出力データ

出力される JSON ファイルは以下のようなフラット構造になります：

```json
[
  {
    "id": "13000-6-1-1-1",
    "facility_id": "13000-6-1-1",
    "manager_type_id": "13000",
    "department_id": "6",
    "facility_type_id": "1",
    "facility_seq_id": "1",
    "toilet_seq_id": "1",
    "facility_name": "千代田合同庁舎",
    "prefecture": "東京都",
    "address": "千代田区内神田二丁目1番12号",
    "building_name": "千代田合同庁舎",
    "toilet_name": "車椅子使用者対応トイレ",
    "floor": "1F",
    "gender_type": "共用",
    "door_type": "C.手動引き戸",
    "location": {
      "longitude": 139.768232,
      "latitude": 35.688985,
      "coordinate_system": "JGD2011"
    },
    "features": {
      "has_braille_blocks": false,
      "has_voice_guidance": false,
      "is_wheelchair_accessible": true,
      "has_wheelchair_turning_space": true,
      "has_backrest": false,
      "has_handrails": true,
      "has_ostomate_facilities": null,
      "has_warm_water_ostomate": false,
      "has_large_bed": false,
      "has_diaper_changing_table": false,
      "has_baby_chair": false,
      "has_emergency_call_button": true
    },
    "opening_hours": [
      {
        "day": "monday",
        "day_name": "月曜日",
        "season": 1,
        "hours": {
          "start": "08:00",
          "end": "16:45"
        }
      }
      // ... 他の曜日 ...
    ],
    "has_consistent_hours": true,
    "other_hours_info": null,
    "notes": null,
    "photos": {
      "entrance": null,
      "inside": null,
      "inside_alt": null
    },
    "metadata": {
      "created_date": "2024-01",
      "updated_date": "2024-02"
    }
  }
  // ... 他のトイレ ...
]
```

## データ構造のポイント

1. **フラット構造の採用**

   - 各トイレが独立したレコードとして出力され、階層構造を持たない
   - すべての情報（施設情報とトイレ情報）が 1 つのオブジェクトに含まれる

2. **一意の識別子**

   - 各トイレに一意の ID（`id`）を付与
   - ID は「管理者種別番号-部局番号-施設種別番号-施設通し番号-トイレ通し番号」の形式
   - 施設 ID も「管理者種別番号-部局番号-施設種別番号-施設通し番号」の形式で提供

3. **関連データのグループ化**

   - 位置情報（経度・緯度）は `location` オブジェクトにグループ化
   - バリアフリー機能は `features` オブジェクトにグループ化
   - 写真データは `photos` オブジェクトにグループ化
   - メタデータ（作成日・更新日）は `metadata` オブジェクトにグループ化

4. **営業時間の配列化**

   - 曜日ごとの営業時間を `opening_hours` 配列にまとめる
   - 各営業時間には曜日情報（英語・日本語）とシーズン情報を含む
   - シーズンによる営業時間の違いも同一形式で表現

## データフィルタリング

以下のフィルタリングが適用されます：

- `deleted_date` フィールドに値があるデータは出力から除外されます
- 変換処理中に除外されたレコード数が表示されます

## 時間の解析

営業時間は以下のように解析されます：

- 「0800_1645」→ `{"start": "08:00", "end": "16:45"}`
- 「8:30 ～ 19:00」→ `{"start": "8:30", "end": "19:00"}`
- 「9 時～ 17 時 30 分」→ `{"start": "9時", "end": "17時30分"}`
- 「24 時間営業」→ `{"start": "00:00", "end": "24:00"}`
- 解析できない形式 → `{"note": "元の文字列", "start": null, "end": null}`
- 空欄（NaN） → `{"start": null, "end": null}`

## 日付の変換

日付データは ISO 8601 形式に変換されます：

- 「202401.0」→ `"2024-01"`（YYYY-MM 形式）
- 「20240105.0」→ `"2024-01-05"`（YYYY-MM-DD 形式）
- すでに ISO 形式のデータはそのまま保持
- `null`（欠損値） → `null`

## 真偽値と欠損値の変換

スクリプトでは以下のように変換されます：

- ○、◯、丸、マル → `true`
- ×、✕、☓、バツ → `false`
- 有 → `true`
- 無 → `false`
- 欠損値（NaN）→ `null`

## 列名の対応表

主な日本語列名と英語列名の対応は以下の通りです：

| 日本語列名                                       | 英語列名                     |
| ------------------------------------------------ | ---------------------------- |
| 施設名                                           | facility_name                |
| トイレ名                                         | toilet_name                  |
| 設置フロア                                       | floor                        |
| 経度                                             | longitude                    |
| 緯度                                             | latitude                     |
| 性別の分け                                       | gender_type                  |
| トイレへの誘導路として点字ブロックを敷設している | has_braille_blocks           |
| トイレの位置等を音声で案内している               | has_voice_guidance           |
| 戸の形式                                         | door_type                    |
| 車椅子が出入りできる                             | is_wheelchair_accessible     |
| 車椅子が転回できる                               | has_wheelchair_turning_space |
| 月曜日                                           | monday_hours                 |
| データの作成年月                                 | created_date                 |
| データの変更年月                                 | updated_date                 |
| データの削除年月                                 | deleted_date                 |

## 注意事項

- 入力 CSV ファイルのエンコーディングは UTF-8 または Shift-JIS を自動判別します
- データによっては一部の列が存在しない場合がありますが、スクリプトはエラーにならずに処理を続行します
- 空のセル（NaN 値）はすべて `null` に変換されます
- 営業時間データは様々な形式（「0800_1645」、「8:30 ～ 19:00」など）に対応していますが、複雑な形式は解析できない場合があります
- 日付データは自動的に ISO 8601 形式（YYYY-MM または YYYY-MM-DD）に正規化されます
- `deleted_date` に値があるデータはすべて出力から除外されます

## ライセンス

このツールは自由に使用・改変・再配布が可能です。
