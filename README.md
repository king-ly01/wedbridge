# wework-dify-bridge 使用文档

企业微信智能机器人 + Dify 工作流 桥接服务，通过长连接 WebSocket 接收企微消息，转发给 Dify 工作流处理后回复用户。

---

## 目录

1. [项目结构](#1-项目结构)
2. [安装依赖](#2-安装依赖)
3. [config.json 配置说明](#3-configjson-配置说明)
4. [获取各配置项的方法](#4-获取各配置项的方法)
5. [启动与停止](#5-启动与停止)
6. [Dify 工作流配置要求](#6-dify-工作流配置要求)
7. [Dify HTTP 通知节点配置](#7-dify-http-通知节点配置)
8. [数据流示意](#8-数据流示意)
9. [Dify Squid 代理白名单配置](#9-dify-squid-代理白名单配置)
10. [常见问题排查](#10-常见问题排查)

---

## 1. 项目结构

```
wework-dify-bridge/
├── wework_smart_bot_final.py   # 主程序（一般不需要修改）
├── config.json                 # ⭐ 所有配置，只需修改这一个文件
├── bridge.log                  # 运行日志（自动生成）
└── README.md                   # 本文档
```

---

## 2. 安装依赖

### Linux / macOS

```bash
pip install wecom-aibot-sdk-python aiohttp --break-system-packages
```

### Windows

需先安装 [Python 3.8+](https://www.python.org/downloads/)（安装时勾选 **Add Python to PATH**），然后：

```bat
start.bat install
```

---

## 3. config.json 配置说明

```json
{
  "wecom": {
    "bot_id": "企业微信智能机器人的 Bot ID",
    "secret": "企业微信智能机器人的 Secret"
  },
  "dify": {
    "api_base": "http://127.0.0.1/v1",
    "api_key": "app-xxxxxxxxxxxxxxxxxxxxxxxx",
    "input_variable": "input",
    "output_variable": "text",
    "timeout": 60
  },
  "service": {
    "welcome_message": "你好！我是 AI 助手，有什么可以帮你的吗？",
    "thinking_message": "⏳ 思考中...",
    "log_level": "INFO",
    "notify_port": 8899,
    "notify_url_for_dify": "http://172.18.0.1:8899/notify",
    "default_chatid": "填入目标会话的 chatid"
  }
}
```

### 字段说明

| 字段 | 说明 |
|------|------|
| `wecom.bot_id` | 企业微信智能机器人的 Bot ID |
| `wecom.secret` | 企业微信智能机器人的 Secret |
| `dify.api_base` | Dify 服务地址，本机部署默认 `http://127.0.0.1/v1` |
| `dify.api_key` | Dify 工作流应用的 API 密钥，格式为 `app-xxx` |
| `dify.input_variable` | 工作流开始节点的输入变量名，默认 `input` |
| `dify.output_variable` | 工作流结束节点的输出变量名，默认 `text` |
| `dify.timeout` | 等待 Dify 响应的超时秒数，默认 60 |
| `service.welcome_message` | 用户进入会话时的欢迎语 |
| `service.thinking_message` | 调用 Dify 期间显示的等待提示 |
| `service.log_level` | 日志级别：DEBUG / INFO / WARNING |
| `service.notify_port` | 本地通知接口端口，默认 8899 |
| `service.notify_url_for_dify` | Dify HTTP 节点调用本服务的 URL（填入 Dify HTTP 节点） |
| `service.default_chatid` | 默认发送目标会话 ID，Dify HTTP 节点不传 chatid 时使用 |

---

## 4. 获取各配置项的方法

### 4.1 获取 bot_id 和 secret

1. 登录企业微信管理后台：https://work.weixin.qq.com
2. 进入「应用管理」→「智能机器人」
3. 找到你的机器人，查看 Bot ID 和 Secret

### 4.2 获取 Dify API 密钥

1. 打开 Dify，进入目标工作流应用
2. 点击右上角「API 访问」或「发布」→「访问 API」
3. 复制 API 密钥（格式为 `app-xxx`）

### 4.3 获取 default_chatid

1. 启动桥接服务（见第 5 节）
2. 在企业微信里，向机器人发任意一条消息
3. 查看日志：

```bash
tail -f /home/linyang/wework-dify-bridge/bridge.log
```

4. 找到类似这行：

```
[收到] 张三 (chatid=wreVEBEgAAdFURgpJ8RLuU7kZagJklxQ): 你好
```

5. 将 `chatid=` 后面的值填入 config.json 的 `default_chatid`，重启服务。

### 4.4 确认 notify_url_for_dify 的 IP

`172.18.0.1` 是 Dify Docker 容器访问宿主机的网桥 IP，可通过以下命令确认：

```bash
docker network inspect docker_default | grep Gateway
# 或
ip addr show docker0
```

---

## 5. 启动与停止

### Linux / macOS

```bash
chmod +x start.sh
./start.sh start     # 启动
./start.sh stop      # 停止
./start.sh restart   # 重启
./start.sh status    # 查看状态
./start.sh log       # 实时查看日志
```

### Windows

双击 `start.bat` 直接启动，或在命令行：

```bat
start.bat install    # 首次安装依赖
start.bat start      # 启动
start.bat stop       # 停止
start.bat restart    # 重启
start.bat status     # 查看状态
start.bat log        # 查看最近日志
```

> Windows 下如需开机自启，可用任务计划程序或 NSSM（见下方说明）。

### Windows 开机自启（可选，使用任务计划程序）

1. 打开「任务计划程序」→「创建基本任务」
2. 触发器选「计算机启动时」
3. 操作选「启动程序」→ 选择 `start.bat`，起始于填写解压目录

---

## 6. Dify 工作流配置要求

### 6.1 开始节点

必须有一个文本输入变量，变量名与 config.json 的 `input_variable` 保持一致：

```
变量名：input
类型：文本输入
必填：是
```

### 6.2 结束节点（End Node）

结束节点的输出变量名必须与 config.json 的 `output_variable` 保持一致：

```
输出变量名：text
引用来源：选择 LLM节点 → 字段选 text
```

> ⚠️ **重要**：Dify LLM 节点的输出字段名是 `text`，**不是** `message`。
> 如果选错了 `.message`，企微机器人会回复空内容 `{}`。

**正确配置示例：**

```yaml
outputs:
  - value_selector:
      - "LLM节点的ID"
      - text          # ← 必须是 text，不是 message
    value_type: string
    variable: text    # ← 必须是 text，与 output_variable 一致
```

### 6.3 DSL 导入方式

修改 DSL 文件（.yml）后，需要手动导入 Dify 才能生效：

1. 打开 Dify → 进入目标工作流
2. 点击右上角「...」→「导入 DSL」
3. 选择修改后的 `.yml` 文件上传
4. 确认覆盖，重新发布工作流

---

## 7. Dify HTTP 通知节点配置

当工作流需要在中间步骤主动推送消息给企微用户时，添加 HTTP 节点：

### 节点配置

| 字段 | 值 |
|------|-----|
| URL | `http://172.18.0.1:8899/notify` |
| Method | POST |
| Headers | `Content-Type:application/json` |
| Body 类型 | Raw Text |
| Body 内容 | `{"content":"{{#LLM节点ID.text#}}"}` |

### Body 格式说明

`/notify` 接口支持两种 Body 格式：

**简化格式（推荐）：**
```json
{"content": "要发送的消息内容"}
```

**企微原生格式（兼容）：**
```json
{"msgtype": "text", "text": {"content": "要发送的消息内容"}}
```

- `chatid` 字段可省略，省略时自动使用 config.json 中的 `default_chatid`
- 消息以 **Markdown** 格式发送，支持加粗、换行等格式

---

## 8. 数据流示意

```
企微用户发消息
      │
      ▼
桥接服务（wework_smart_bot_final.py）
  │  接收消息，提取 sender 和 chatid
  │  先回复"⏳ 思考中..."
      │
      ▼
调用 Dify 工作流（POST /workflows/run）
  │  传入：inputs.input = 用户消息
  │        inputs.chatid = 会话 ID
      │
      ▼
Dify 工作流运行
  │  （可选）中途通过 HTTP 节点
  │          POST /notify 主动推送消息 ──→ 企微用户收到中间消息
  │
  │  工作流结束，返回 outputs.text
      │
      ▼
桥接服务将 outputs.text 发回企微用户
```

---

## 9. Dify Squid 代理白名单配置

Dify 的所有 HTTP 节点请求都经过内置的 squid 代理（SSRF 防护），默认只允许公网地址。若要让 Dify HTTP 节点访问宿主机的桥接服务，**必须**手动将宿主机 IP 和端口加入白名单。

### 9.1 配置文件位置

```
/home/linyang/dify/docker/ssrf_proxy/squid.conf.template
```

### 9.2 需要添加的内容

在文件的 `http_access deny all` **之前**添加以下三行：

```
acl notify_host dst 172.18.0.1
acl notify_port port 8899
http_access allow notify_host notify_port
```

**完整示意（关键部分）：**

```
...
http_access allow localhost
include /etc/squid/conf.d/*.conf
# ↓ 新增：允许 Dify 容器访问宿主机桥接服务
acl notify_host dst 172.18.0.1
acl notify_port port 8899
http_access allow notify_host notify_port
# ↑ 新增结束
http_access deny all         # ← 必须在这行之前
...
```

> ⚠️ `172.18.0.1` 是 Dify Docker 网桥网关 IP（宿主机侧），请先用以下命令确认：
> ```bash
> docker network inspect docker_default | grep Gateway
> ```
> 如果 IP 不同，请同步修改 squid 配置和 config.json 中的 `notify_url_for_dify`。

### 9.3 使配置生效

修改 squid.conf.template 后，需要重建 ssrf_proxy 容器：

```bash
cd /home/linyang/dify/docker
docker compose restart ssrf_proxy
```

或完整重启 Dify：

```bash
docker compose down && docker compose up -d
```

### 9.4 验证是否生效

重启后查看 squid 访问日志，再在 Dify 里触发一次 HTTP 节点，日志中应出现 `TCP_MISS/200`：

```bash
docker exec -it docker-ssrf_proxy-1 tail -f /var/log/squid/access.log
```

- `TCP_MISS/200` → 请求通过，正常
- `TCP_MISS/500` → 桥接服务返回错误（检查 bridge.log）
- `CONNECT/403` 或 `TCP_DENIED` → 白名单未生效，检查配置顺序

---

## 10. 常见问题排查

### 问题：企微机器人回复 `{}`

**原因**：结束节点的输出变量引用了 LLM 节点的 `.message` 字段，但实际字段名是 `.text`。

**修复**：打开 DSL 文件，找到所有结束节点（`type: end`），将：
```yaml
- '某LLM节点ID'
- message       # ← 错误
variable: message
```
改为：
```yaml
- '某LLM节点ID'
- text          # ← 正确
variable: text
```
然后重新导入 DSL。

---

### 问题：HTTP 节点报 400 错误

**原因**：Body 中 `content` 字段为空，通常是引用了错误的变量路径。

**检查**：确认 HTTP 节点 Body 中引用的变量路径正确，如 `{{#节点ID.text#}}`，而不是 `{{#节点ID.message#}}`。

---

### 问题：HTTP 节点报 500 / `Invalid control character`

**原因**：Dify 变量展开后包含换行符等控制字符，导致 JSON 解析失败。

**结论**：桥接服务已内置处理，如仍出现请检查 bridge.log 中的具体错误信息。

---

### 问题：`Reached maximum retries` / 连接失败

**原因**：Dify 容器无法访问宿主机的 8899 端口。

**检查步骤**：
1. 确认桥接服务正在运行：`ps aux | grep wework_smart_bot_final`
2. 确认 squid 代理白名单包含 `172.18.0.1`
3. 确认 `notify_url_for_dify` 中的 IP 是正确的网桥地址

---

### 问题：修改 config.json 后不生效

config.json 在服务启动时读取一次，修改后需要重启服务：

```bash
pkill -f wework_smart_bot_final.py && sleep 1
nohup python3 /home/linyang/wework-dify-bridge/wework_smart_bot_final.py > /home/linyang/wework-dify-bridge/bridge.log 2>&1 &
```

---

### 问题：Dify 工作流 LLM 节点冲突检测失效（重复预订）

**原因**：Supabase `get_rows` 节点的数据在 `json` 字段（不是 `text` 字段），且时间格式为 `HH:MM:SS`（含秒）。

**修复**：
- User Prompt 中引用数据应使用 `{{#节点ID.json#}}`，而非 `{{#节点ID.text#}}`
- System Prompt 中需说明时间比较方式：截取前5位 `HH:MM` 后再比较

---

*文档生成时间：2026-04-16*
