#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import argparse
import sys
import os
import glob
import pathlib

def compact_json(input_file, output_dir=None):
    """JSONファイルをインデントなしのコンパクトな形式に変換する関数"""
    try:
        # JSONファイルを読み込む
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 出力先が指定されている場合
        if output_dir:
            # 出力ディレクトリがなければ作成
            os.makedirs(output_dir, exist_ok=True)
            
            # 入力ファイル名を取得
            filename = os.path.basename(input_file)
            output_file = os.path.join(output_dir, filename)
            
            # コンパクトなJSONとして保存
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
            print(f"コンパクトなJSONを {output_file} に保存しました。")
        else:
            # 出力先が指定されていない場合は標準出力に出力
            json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            print(json_str)
            
    except FileNotFoundError:
        print(f"エラー: ファイル '{input_file}' が見つかりません。", file=sys.stderr)
        return 1
    except json.JSONDecodeError:
        print(f"エラー: '{input_file}' は有効なJSONファイルではありません。", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1
    
    return 0

def process_directory(input_path, output_dir):
    """ディレクトリ内のすべてのJSONファイルを処理する"""
    if os.path.isdir(input_path):
        # 入力がディレクトリの場合、すべてのJSONファイルを処理
        json_files = glob.glob(os.path.join(input_path, "*.json"))
        
        if not json_files:
            print(f"警告: '{input_path}' にJSONファイルが見つかりませんでした。")
            return 1
        
        errors = 0
        for json_file in json_files:
            result = compact_json(json_file, output_dir)
            if result != 0:
                errors += 1
        
        if errors > 0:
            print(f"{errors}個のファイルでエラーが発生しました。")
            return 1
        
        return 0
    else:
        # 入力が単一ファイルの場合
        return compact_json(input_path, output_dir)

def main():
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description='JSONファイルをインデントなしのコンパクトな形式に変換します。')
    parser.add_argument('input_path', help='入力JSONファイルまたはディレクトリのパス')
    parser.add_argument('-o', '--output', default='json_min', help='出力ディレクトリ（デフォルト: json_min）')
    
    args = parser.parse_args()
    
    return process_directory(args.input_path, args.output)

if __name__ == '__main__':
    sys.exit(main()) 