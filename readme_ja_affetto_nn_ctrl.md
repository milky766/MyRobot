# affetto-nn-ctrl

Affetto用ニューラルネットワークを用いたデータ駆動型コントローラ

## 概要

このプロジェクトでは、ニューラルネットワークを用いて入力遅延を補償する、Affetto用のデータ駆動型コントローラを開発しています。本リポジトリには、以下の機能が含まれています：

* Affettoのランダムな動作中に、センサデータとアクチュエータデータを収集するツール
* キネスティックティーチングを用いた関節角度の軌道記録ツール
* 特定の遅延を補償する多層パーセプトロン（MLP）モデルの学習機能
* ニューラルネットワークベースのコントローラと従来のPIDコントローラの追従性能の比較評価機能

## はじめに

### 依存関係

このソフトウェアは Python で書かれており、[uv](https://docs.astral.sh/uv/) によって管理されています。`uv` をインストールするには以下を実行します：

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### インストール

リポジトリをクローンし、仮想環境内に依存関係をインストールします：

```shell
git clone https://github.com/hrshtst/affetto-nn-ctrl.git
cd affetto-nn-ctrl
uv sync
```

仮想環境内でプログラムを実行するには、以下のようにします：

```shell
uv run python apps/collect_data.py -h
```

### 設定

外部ストレージにデータを保存する場合、デフォルトの出力ディレクトリを `apps/base_dir` というファイルで指定できます：

```shell
echo "/mnt/data-storage/somewhere" > apps/base_dir
```

`base_dir` が指定されておらず、`-b/--base-dir` オプションもない場合は、出力ディレクトリは `./data` になります。

### テスト実行

テストスイートを実行するには以下を使います：

```shell
uv run pytest
```

## アプリケーションの使い方

### データ収集

`apps/collect_data.py` を用いてランダム動作データを収集します。以下は、左肘関節（関節ID: 5）のデータを60秒間、100回繰り返しで収集する例です：

```shell
uv run python apps/collect_data.py -v \
  --init-config "apps/config/init_left_elbow.toml" \
  --config "apps/config/affetto.toml" \
  --joints 5 -T 60 -s 12345 -t 0.1 1.0 -q 20 40 \
  -p step --no-async-mode -n 100 \
  --label "left_elbow" --sublabel "step/sync/fast" --no-overwrite
```

他のオプションについては `-h` オプションを参照してください。

### モデル学習

`apps/train_model.py` を用いて、収集したデータでMLPモデルを学習できます。以下は、リファレンス予測前処理と標準偏差スケーリングを用いた例です（データセットの25%をランダム選択）：

```shell
label="left_elbow"; cont=step; sync=sync; scale=fast
a=preview-ref.default; s=std.default; r=mlp.default
uv run python apps/train_model.py -v \
  /mnt/data-storage/somewhere/affetto_nn_ctrl/dataset/left_elbow/20241203T144115/${cont}/${sync}/${scale} \
  -j 5 --train-size 0.25 --seed 42 \
  -m apps/config/model.toml \
  -a ${a} -s ${s} -r ${r} \
  --label "${label}" --sublabel "${a}/${r}/${s}/${cont}_${sync}_${scale}"
```

詳細は `-h` や `model.toml` を参照してください。

### 予測性能評価

`apps/calculate_score.py` を用いて、未知データに対する予測性能（$R^2$スコア）を計算できます。以下は、各スピード（slow, middle, fast）のデータから10%をサンプリングする例です：

```shell
label="left_elbow"; cont=step; sync=sync; scale=fast
a=preview-ref.default; s=std.default; r=mlp.default
uv run python apps/calculate_score.py -v \
  /mnt/data-storage/somewhere/affetto_nn_ctrl/trained_model/left_elbow/latest/${a}/${r}/${s}/${cont}_${sync}_${scale}/trained_model.joblib \
  -d /mnt/data-storage/somewhere/affetto_nn_ctrl/dataset/left_elbow/20241203T144115/${cont}/${sync}/{slow,middle,fast} \
  --test-size 0.1 --split-in-each-directory --seed 42 \
  -e png pdf
```

スコアは `scores.toml` に保存され、時系列プロットも生成されます。

### 参照軌道の記録

`apps/record_trajectory.py` を用いて、関節の位置軌道を記録できます。以下は左肘関節を30秒間記録する例です：

```shell
uv run python apps/record_trajectory.py -v \
  --init-config "apps/config/init_left_elbow.toml" \
  --joints 5 -T 30 --label left_elbow
```

### 追従性能評価

`apps/track_trajectory.py` を用いて、学習済みモデルの追従性能を評価できます。以下は、ある参照軌道を10回繰り返して再生する例です：

```shell
label="left_elbow"; cont=step; sync=sync; scale=fast
a=preview-ref.default; s=std.default; r=mlp.default
uv run python apps/track_trajectory.py -v \
  /mnt/data-storage/somewhere/affetto_nn_ctrl/trained_model/left_elbow/latest/${a}/${r}/${s}/${cont}_${sync}_${scale}/trained_model.joblib \
  --init-config "apps/config/init_left_elbow.toml" \
  --joints 5 \
  -r /mnt/data-storage/somewhere/affetto_nn_ctrl/reference_trajectory/left_elbow/20241219T111141/reference_trajectory_000.csv \
  -n 10
```

PID制御との比較を行う場合は、モデルパスを省略します：

```shell
uv run python apps/track_trajectory.py -v \
  --init-config "apps/config/init_left_elbow.toml" \
  --joints 5 \
  -r /mnt/data-storage/somewhere/affetto_nn_ctrl/reference_trajectory/left_elbow/20241219T111141/reference_trajectory_000.csv \
  -n 10
```

結果は `tracked_trajectory.toml` に保存されます。

### RMSEの計算

`apps/calculate_rmse.py` を用いて、実際の軌道と参照軌道とのRMSE（平均二乗誤差平方根）を計算します：

```shell
label="left_elbow"; cont=step; sync=sync; scale=fast
a=preview-ref.default; s=std.default; r=mlp.default
uv run python apps/calculate_rmse.py -v \
  /mnt/data-storage/somewhere/affetto_nn_ctrl/trained_model/left_elbow/latest/${a}/${r}/${s}/${cont}_${sync}_${scale}/track_performance/latest/tracked_trajectory.toml \
  --fill --fill-err-type std --fill-alpha 0.2 \
  -e png pdf
```

RMSE値は `tracked_trajectory.toml` に追記され、対応するプロットも出力ディレクトリに保存されます。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

