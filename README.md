# Realsense_Recorder

## 必要ライブラリ

- Python 3
- numpy
- python-opencv
- pyrealsense2

anacondaの環境は`env.yaml`にあります

### 環境構築

```
> conda env create -n realsense -f env.yaml
> conda activate realsense
```

## 使い方

### hayakawa

```
> cd hayakawa
-- 録画(横640ピクセル, 10秒)
hayakawa > python record.py -w 640 -t 10
-- 再生
hayakawa > python replay.py 2022-04-23-23-12-50.json 
```

オプション

```
hayakawa>python record.py -h
usage: record.py [-h] [-w WIDTH] [--height HEIGHT] [-t TIME] [-f FREQ]
                 [-o OUT] [-d {blend,stack}]

optional arguments:
  -h, --help            show this help message and exit
  -w WIDTH, --width WIDTH
                        horizontal resolution
  --height HEIGHT       vertical resolution
  -t TIME, --time TIME  recording time in second
  -f FREQ, --freq FREQ  camera frequency
  -o OUT, --out OUT     out directory
  -d {blend,stack}, --display {blend,stack}
                        display method
```

```
hayakawa>python replay.py -h 
usage: replay.py [-h] [-d {blend,stack}] json

positional arguments:
  json                  configuration file path

optional arguments:
  -h, --help            show this help message and exit
  -d {blend,stack}, --display {blend,stack}
                        display method
```
