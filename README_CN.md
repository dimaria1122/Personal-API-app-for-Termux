# Telegram Termux 自动签到

这是一个在 Android 手机上用 Termux 运行的 Telegram 自动签到工具，支持三个个人账号和两种调度模式：

- `calendar_day`：过本地零点后可签到。
- `interval_after_success`：以上次成功签到时间为基准，间隔到点后再签到。

用途只限你自己的 Telegram 账号和正常签到流程，不做验证码绕过、风控绕过或封禁规避。

## 你手机上要怎么操作

先把仓库拉到手机里。两种常见方式：

1. 如果仓库已经在 GitHub 上，直接在 Termux 里执行：

```bash
pkg update -y
pkg install -y git
git clone <你的仓库地址> teleg
cd teleg
```

2. 如果你是从电脑传到手机的，先把整个项目文件夹复制到手机，再在 Termux 里进入这个目录：

```bash
cd /sdcard/Download/teleg
```

如果你要读写手机下载目录，先执行一次：

```bash
termux-setup-storage
```

## 一次性安装

在项目目录里运行：

```bash
bash scripts/setup_termux.sh
```

它会安装：

- Python
- Git
- termux-api
- Python 依赖

## 配置账号

先复制示例配置：

```bash
cp config/accounts.example.yaml config/accounts.yaml
cp config/tasks.example.yaml config/tasks.yaml
```

然后编辑 `config/accounts.yaml`，把三个账号的手机号和 session 名写进去。示例：

```yaml
accounts:
  - name: main
    phone: "+8613800000000"
    session: account_1
  - name: alt1
    phone: "+8613900000000"
    session: account_2
  - name: alt2
    phone: "+8615000000000"
    session: account_3
```

`session` 只是本地会话文件名，不是 Telegram 密码。

## Telegram API 凭证

这个仓库里已经放了一个临时公开后备值，先保证你能跑通流程。

如果你自己的 `api_id/api_hash` 已经申请好，在 Termux 里新建覆盖文件：

```bash
cat > ~/.tg-sign.env <<'EOF'
export TELEGRAM_API_ID=123456
export TELEGRAM_API_HASH=0123456789abcdef0123456789abcdef
EOF
chmod 600 ~/.tg-sign.env
```

优先级是：

1. `~/.tg-sign.env`
2. 仓库里的 `config/public-api.env`

## 登录三个账号

第一次要先登录三个 Telegram 账号，生成本地 session：

```bash
bash scripts/login_accounts.sh
```

运行后会按账号逐个让你输入 Telegram 验证码。如果开了两步验证，还要输入密码。

## 配置签到任务

编辑 `config/tasks.yaml`。有两种任务：

### 1. 过零点就能签

```yaml
- name: midnight_bot
  bot: "@example_midnight_bot"
  command: "/checkin"
  accounts: ["main", "alt1", "alt2"]
  schedule:
    mode: calendar_day
    timezone: Asia/Shanghai
    earliest_time: "00:05"
    random_delay_minutes: [5, 45]
```

### 2. 以上次成功时间为基准

```yaml
- name: interval_bot
  bot: "@example_interval_bot"
  command: "/checkin"
  accounts: ["main", "alt1", "alt2"]
  schedule:
    mode: interval_after_success
    min_interval_hours: 24
    random_delay_minutes: [5, 40]
```

## 先试运行

正式跑之前先 dry-run：

```bash
python -m src scheduler --accounts config/accounts.yaml --config config/tasks.yaml --state data/state.json --dry-run
```

你会看到：

- `DUE account:task`
- `SKIP account:task not-due`

## 正式运行

```bash
termux-wake-lock
bash scripts/run_scheduler.sh
```

默认每 5 分钟检查一次。要改间隔，可以先设置：

```bash
export SLEEP_SECONDS=600
```

## 查看状态

```bash
bash scripts/check_status.sh
```

## 手机后台设置

为了让 Termux 不容易被杀掉，建议做这些：

- 关闭 Termux 电池优化。
- 允许后台运行。
- 如果手机支持，给 Termux 自启动权限。
- 把 Termux 锁在最近任务里。
- 长时间运行时先执行 `termux-wake-lock`。

## 常见问题

### 1. 还是提示登录或验证码

这是正常的，第一次登录每个账号都要过一次验证码。

### 2. 没有签到

先运行 dry-run，看任务是不是被判定为 `not-due`。如果状态里已有上次成功时间，可能要等到条件满足。

### 3. 程序被手机杀掉

这是 Android 后台限制，不是代码报错。先按上面的后台设置处理，再重试。

### 4. 想换成自己的 API

把自己的 `TELEGRAM_API_ID` 和 `TELEGRAM_API_HASH` 写进 `~/.tg-sign.env`，重新 source 一次即可。
