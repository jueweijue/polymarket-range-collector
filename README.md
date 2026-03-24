# Polymarket Range Collector

一个面向 **历史数据回补** 的小项目：按**北京时间**配置时间段，批量解析这段时间内所有 **Polymarket BTC Up/Down 5m 场次**，下载 **Binance BTCUSDT aggTrades** 历史文件，并为每个场次重建一份 **5 分钟、逐秒** 的 BTC / YES / NO 数据 Excel。

---

## 这个项目解决什么问题

当你想复盘某个北京时间区间里的 BTC Up/Down 5 分钟市场时，通常会碰到几个麻烦：

1. **BTC 价格**需要精确到秒，普通 K 线粒度不够
2. **Polymarket 场次**要先按时间段一个个解析出来
3. **YES / NO 历史价格**不能直接从一个完美的历史盘口接口里拿到
4. 多个 5 分钟场次一起处理时，人工拉取和导表很低效

这个项目就是把这些步骤串起来，做成一条可重复执行的流水线。

---

## 项目能力

项目目前支持：

- 按北京时间设置起止时间段
- 自动解析这段时间内所有 BTC Up/Down 5m 场次
- 自动下载 Binance 公共历史数据（`BTCUSDT aggTrades` 日线 zip）
- 自动拉取每个场次的 Polymarket 历史 trades
- 按秒重建每个场次 5 分钟窗口内的：
  - BTC 价格
  - YES 价格
  - NO 价格
- 每个场次输出一个独立 Excel
- 输出完整性标记：`COMPLETE` / `BEST_EFFORT`

---

## 重要边界：它不是“历史订单簿回放器”

这个点必须说清楚。

### 能拿到的历史数据
- **Binance BTC 历史成交**：可以从 `data.binance.vision` 下载 zip 回补
- **Polymarket 历史 trades**：可以通过 Data API 拉取并重建

### 拿不到的历史数据
- **Polymarket 历史 orderbook 快照 / 深度回放**：公共接口没有提供完整可回放的历史盘口流

所以现在这个项目里：

- **BTC Price** = Binance `aggTrades` 重建出的每秒最后成交价
- **YES / NO Price** = Polymarket 历史 trades 重建出的“截至该秒最后一笔已知成交价”

也就是说，当前版本是一个：

> **历史成交驱动的逐秒价格重建器**

不是：

> **历史盘口深度回放器**

如果你未来自己有实时保存下来的盘口快照，这个项目可以继续升级成“盘口版”。

---

## 目录结构

> 说明：`data/`、`output/` 里的运行时文件和子目录会在程序首次运行时自动创建，不需要手动 mkdir。


```text
polymarket-range-collector/
├── .gitignore
├── README.md
├── requirements.txt
├── run.py
├── config/
│   ├── config.example.json
│   └── config.test.json
├── src/
│   └── collector.py
├── data/
│   ├── binance/        # 下载的 Binance zip
│   ├── trades/         # 每个场次的历史 trades JSON
│   └── markets.json    # 当前配置范围解析出的场次清单
└── output/
    └── *.xlsx          # 每个场次单独 Excel
```

---

## 环境要求

- Python 3.10+
- 依赖：
  - `openpyxl`
- 网络访问：
  - `gamma-api.polymarket.com`
  - `data-api.polymarket.com`
  - `data.binance.vision`

安装依赖：

```bash
pip install -r requirements.txt
```

---

## 配置方式

先复制一份配置：

```bash
cp config/config.example.json config/config.json
```

然后编辑 `config/config.json`：

```json
{
  "range": {
    "start_bjt": "2026-03-17 23:45:00",
    "end_bjt": "2026-03-18 00:00:00"
  },
  "polymarket": {
    "filter_amount": 0
  }
}
```

### 配置项说明

#### `range.start_bjt`
- 北京时间起点
- 格式：`YYYY-MM-DD HH:MM:SS`

#### `range.end_bjt`
- 北京时间终点
- 格式：`YYYY-MM-DD HH:MM:SS`

#### `polymarket.filter_amount`
- 传给 Polymarket Data API 的 `filterAmount`
- 默认 `0` 表示尽量全量抓取
- 如果你只关心较大成交，可以设更高值，但会损失小单信息

---

## 使用方式

### 一、总控脚本（推荐）

总控脚本路径：

```bash
python3 run.py <action>
```

支持的 action：

- `prepare`
- `history`
- `export`
- `all`

---

### 二、步骤详解

#### 1) 预处理

```bash
python3 run.py prepare
```

做两件事：

1. 解析配置时间段内有哪些 BTC Up/Down 5m 场次
2. 下载对应日期的 Binance `BTCUSDT-aggTrades-YYYY-MM-DD.zip`

输出结果：
- `data/markets.json`
- `data/binance/*.zip`

如果某一天的 Binance 日线 zip 还没发布，程序会提示 `pending`，不会中断。

---

#### 2) 拉历史 trades

```bash
python3 run.py history
```

会按场次：

- 调用 Polymarket Data API 拉历史成交
- 做分页
- 做 `BUY` / `SELL` 分片抓取
- 做 recovery ladder 补捞
- 保存到 `data/trades/<slug>.json`

这一步的目标是：

> 尽量避免高成交场次因为分页导致数据被截断

---

#### 3) 导出 Excel

```bash
python3 run.py export
```

会把：

- Binance 历史 BTC 价格
- Polymarket 历史 trades

合并重建成每个场次的逐秒数据，并输出 Excel。

---

#### 4) 一把跑完

```bash
python3 run.py all
```

等价于依次执行：

```bash
python3 run.py prepare
python3 run.py history
python3 run.py export
```

---

## Excel 输出说明

每个场次会输出一个文件：

```text
output/btc-updown-5m-<start_ts>.xlsx
```

例如：

```text
output/btc-updown-5m-1773762300.xlsx
```

### Sheet 1: `Market Timeline`

按秒输出整个 5 分钟窗口（`Sec = 0 ~ 300`）：

- `Sec`
- `Time (UTC)`
- `Time (BJT)`
- `BTC Price`
- `YES Price`
- `NO Price`
- `YES Last Trade (UTC)`
- `NO Last Trade (UTC)`
- `YES Age`
- `NO Age`

### Sheet 2: `Summary`

包含：

- 场次标题
- slug
- condition id
- 起止时间
- 历史 trades 数量
- 完整性状态
- 数据来源说明

---

## 价格重建逻辑

### BTC Price 重建

数据源：
- Binance `BTCUSDT aggTrades` 日线 zip

逻辑：
- 使用 zip 文件中的**微秒时间戳**
- 每秒取该秒最后一笔成交价
- 如果某秒没有成交，则沿用上一秒价格

---

### YES / NO Price 重建

数据源：
- Polymarket Data API 历史 trades

逻辑：
- 遍历该场次历史 trades
- 对每一秒，取**截至该秒最后一笔已知成交价**
- 分别维护 YES / NO 两条价格线

这意味着它表达的是：

> 到这一秒为止，市场最近一次成交所反映的 YES / NO 价格状态

---

## 完整性与风险控制

### 为什么要做完整性标记

Polymarket Data API 在高成交场次下可能存在分页截断风险。

如果只做简单 offset 翻页，可能会漏数据。

### 当前策略

程序会：

- 按 `BUY` / `SELL` 分片抓取
- 自动翻页
- 对疑似截断场次做 recovery ladder 补捞
- 输出完整性状态：
  - `COMPLETE`
  - `BEST_EFFORT`

### 含义

- `COMPLETE`：当前抓取逻辑下未发现未解决的分页风险
- `BEST_EFFORT`：程序已尽量补捞，但不能 100% 证明完全无缺失

对批量历史回补来说，这比直接 hard fail 更实用。

---

## 一个典型流程

假设你要回补北京时间 `2026-03-17 23:45:00` 到 `2026-03-18 00:00:00`：

```bash
cd /root/project/polymarket-range-collector
cp config/config.example.json config/config.json
# 编辑 config/config.json
python3 run.py all
```

运行完后，你会拿到：

- 解析好的场次列表
- Binance 历史数据 zip
- 每个场次的历史 trades JSON
- 每个场次独立 Excel

---

## 适合的使用场景

这个项目适合：

- 批量复盘 BTC Up/Down 5m 市场
- 做策略研究
- 做逐秒时间序列导出
- 做场次级 Excel 报表归档
- 给后续建模/特征工程准备原始逐秒表

---

## 后续可以继续扩展的方向

如果后面你要继续升级，这几个方向最有价值：

1. **汇总总表**
   - 给整个时间段生成一个 index.xlsx
   - 汇总每个场次的结果、trade 数、完整性状态

2. **更多衍生列**
   - YES-NO spread
   - 中间价
   - 最近 N 秒波动
   - 价格变化速度

3. **多日批量回补**
   - 一次跑整天 / 整周 / 多天

4. **接入你自己的历史盘口快照**
   - 把当前 trades 重建版升级成盘口回放版

---

## 当前结论

这个仓库现在是一个：

> **面向历史回补的 BTC Up/Down 5m 场次逐秒重建工具**

用它可以稳定批量地产出每个场次的 Excel，适合你后面继续做研究和复盘。
