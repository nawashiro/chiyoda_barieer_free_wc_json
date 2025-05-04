# JSON 圧縮ツール

`compact_json.py`は JSON ファイルをインデントのないコンパクトな形式に変換するツールです。ディレクトリ内の全 JSON ファイルを一括処理することも可能です。

## 機能

- JSON ファイルのインデントを削除してコンパクトな形式に変換
- 単一ファイルまたはディレクトリ内の全 JSON ファイルを一括処理
- 処理したファイルは自動的に`json_min`ディレクトリに保存（出力先変更可能）
- ファイル名は元のファイル名を維持

## 使い方

### 基本的な使い方

```bash
python compact_json.py 入力ファイルまたはディレクトリ [-o 出力ディレクトリ]
```

### コマンドラインオプション

- `入力ファイルまたはディレクトリ`: 処理する JSON ファイルまたは JSON ファイルを含むディレクトリ
- `-o, --output`: 出力ディレクトリ（指定しない場合は`json_min`ディレクトリに出力）

## 使用例

### 単一ファイルの処理

```bash
# toilet_data.jsonを処理して、json_minディレクトリに保存
python compact_json.py json/toilet_data.json
```

### ディレクトリ内の全 JSON ファイルを処理

```bash
# jsonディレクトリ内の全JSONファイルを処理
python compact_json.py json
```

### 出力先ディレクトリの指定

```bash
# jsonディレクトリ内の全JSONファイルを処理して、compressed_jsonディレクトリに保存
python compact_json.py json -o compressed_json

# toilet_data.jsonを処理して、minifiedディレクトリに保存
python compact_json.py json/toilet_data.json -o minified
```

## 実行例: toilet_data.json の処理

toilet_data.json を処理するには以下のコマンドを実行します：

```bash
python compact_json.py json/toilet_data.json
```

このコマンドは以下の処理を行います：

1. `json/toilet_data.json`ファイルを読み込む
2. インデントを削除してコンパクトな形式に変換
3. `json_min`ディレクトリを自動的に作成（存在しない場合）
4. 変換したファイルを`json_min/toilet_data.json`として保存
5. 処理完了メッセージを表示

## エラー処理

スクリプトは以下のエラーを処理します：

- ファイルが見つからない場合
- 入力ファイルが有効な JSON ではない場合
- ディレクトリに JSON ファイルが存在しない場合
- その他の例外

## 注意事項

- 出力ディレクトリが存在しない場合は自動的に作成されます
- 変換処理は UTF-8 エンコーディングで行われます
- 出力ファイルは入力ファイルと同じ名前で保存されます
