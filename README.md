## About
ユーザが動画をアップロードし,異なるフォーマットや解像度に変換することができるクライアントサーバ分散アプリケーションを作成.

クライアントでは自分のコンピュータからファイルを選択し, 動画をアップロードしたり、選択したサービスに基づいて新しいバージョンの動画をダウンロードしたりできる.

## Contents
1. 動画ファイルの圧縮
2. 解像度変更
3. 縦横比変更
4. オーディオに変換
5. 時間範囲からGIFを作成

* サーバ側では, ffmpegを実行することでこれらを実現する.
* クライアント側ではファイルやコマンドを指定し, jsonファイル(setting.json)にしてサーバ側に送信する.
* client-gui.py ではtkinterを用いてguiで動画やサービスを選択できるようにした.
