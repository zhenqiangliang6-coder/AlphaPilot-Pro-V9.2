交易数据归档目录结构说明
========================

1. 以下是归档目录结构的示例:
.
├── 2020-12-01
│   ├── downfiles
│   │   ├── 346c50af-33b1-11eb-b9c3-001018b67b94
│   │   │   ├── cash.csv
│   │   │   ├── execution_report.csv
│   │   │   ├── func_response.csv
│   │   │   ├── order_status.csv
│   │   │   ├── order_status_change.csv
│   │   │   └── position.csv
│   │   ├── c4d81510-32e1-11eb-993b-001018b67b94
│   │   │   ├── cash.csv
│   │   │   ├── execution_report.csv
│   │   │   ├── func_response.csv
│   │   │   ├── order_status.csv
│   │   │   ├── order_status_change - 副本.csv
│   │   │   ├── order_status_change.csv
│   │   │   └── position.csv
│   │   └── last_modify_time.json
│   ├── events.log
│   └── upfiles
│       └── 某某策略扫单
│           ├── 20201201182037.146974.order.dbf
│           └── 20201201182058.879877.order.dbf
├── 2020-12-02
│   ├── downfiles
│   │   ├── 346c50af-33b1-11eb-b9c3-001018b67b94
│   │   │   ├── cash.csv
│   │   │   ├── execution_report.csv
│   │   │   ├── func_response.csv
│   │   │   ├── order_status.csv
│   │   │   ├── order_status_change.csv
│   │   │   └── position.csv
│   │   ├── c4d81510-32e1-11eb-993b-001018b67b94
│   │   │   ├── cash.csv
│   │   │   ├── execution_report.csv
│   │   │   ├── func_response.csv
│   │   │   ├── order_status.csv
│   │   │   ├── order_status_change.csv
│   │   │   └── position.csv
│   │   └── last_modify_time.json
│   ├── events.log
│   └── upfiles
│       └── 某某策略扫单
│           └── 20201202150324.146916.order.dbf
└── readme.txt

2. 目录名称和文件名称说明
    在归档目录下，包含一个 readme.txt 文件和若干个以日期为命名的子目录。
    其中，readme.txt 即本说明文件。
    以日期方式进行命名的子目录，分别保存对应日期的归档数据。

2.1 日期子目录的结构说明
    在每个日期对应的文件目录下，有2个子目录和1个文件。
    文件 events.log 是记录文件单交易，数据归档功能模块相关的日志信息。
    2个目录分别是：downfiles 和 upfiles。

2.2 downfiles 目录说明
    在 downfiles 目录下，有若干个以交易账户的ID为名称的子目录。在该子目录下，存放该账户在当日的归档的交易数据。
    交易数据按照文件名称，分别保存不同类别的交易数据，下面分别进行说明：
    （1）cash.csv 保存交易账户的资金数据
    （2）position.csv 保存交易账户的持仓数据
    （3）order_status.csv 保存交易账户当日的委托数据
    （4）order_status_change.csv 保存交易账户当日所下委托的状态变化数据
    （5）execution_report.csv 保存交易账户当日所下委托的执行回报
    （6）func_response.csv 保存交易账户当日的功能号指令的执行结果

2.3 upfiles 目录说明
    在 upfiles 目录下，有若干个以 “文件单配置名称” 为名的子目录。在该子目录下，保存了当日向该文件单配置指定的目录下发的所有的文件单原始文件。
