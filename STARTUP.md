# 启动指南

本文档面向**首次运行本项目**的开发者，按顺序执行即可把整套 Web 发布链路跑起来。

> 适用版本：当前 `main` 分支。
>
> 项目概览、各平台账号代码、接口表等仍以 `README.md` 为准；本文只讲"怎么启动"。

---

## 0. 准备环境

- **Python 3.10**（与 `Dockerfile` 一致；其他 3.10+ 版本通常也行，但 Playwright / 部分依赖在更老的版本上可能踩坑）。
- **Node.js**（仅在调试 Vue 前端或构建 Docker 镜像时需要，本地走单文件前端可跳过）。
- **Chromium / Chrome**：本机调试时推荐本机有 Chrome，因为 `conf.LOCAL_CHROME_PATH` 可以指过去；服务器模式由 Playwright 自带的 `chromium-headless-shell` 兜底。
- **端口 `5409`** 空闲（Flask 强制绑定 `0.0.0.0:5409`，改端口要同步改前端和 Dockerfile）。

```bash
python --version          # 应显示 3.10.x
python -m pip --version
```

---

## 1. 拉取代码与初始化

```bash
git clone https://github.com/cxdmnls/social-auto-upload.git
cd social-auto-upload
```

---

## 2. 创建虚拟环境并安装依赖

推荐 `conda`，`venv` 也行：

```bash
# conda 方案
conda create -n social-auto-upload python=3.10
conda activate social-auto-upload

# 或 venv 方案
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
```

安装 Python 依赖 + Playwright 浏览器：

```bash
pip install -r requirements.txt
playwright install chromium
```

> 注意：Dockerfile 用的是 `chromium-headless-shell`，**不需要** `firefox`。`README.md` 里写的 `playwright install chromium firefox` 里 `firefox` 是冗余的，可忽略。

---

## 3. 生成 `conf.py`

仓库根目录的 `conf.example.py` 列出全部 4 个变量（`BASE_DIR`、`LOCAL_CHROME_HEADLESS`、`LOCAL_CHROME_PATH`、`XHS_SERVER`）。直接复制即可：

```bash
cp conf.example.py conf.py
```

按需修改 `conf.py`：

| 变量 | 推荐本地开发值 | 说明 |
| --- | --- | --- |
| `BASE_DIR` | 默认（项目根） | 所有相对路径（`cookiesFile/`、`videoFile/`、`db/`）都挂在它下面。 |
| `LOCAL_CHROME_HEADLESS` | `False` | 扫码时能看到浏览器，方便定位元素。服务器部署改为 `True`。 |
| `LOCAL_CHROME_PATH` | `None` 或本机 Chrome 绝对路径 | `None` 时用 Playwright 自带 Chromium。 |
| `XHS_SERVER` | `http://127.0.0.1:8888` 或 `None` | 小红书的 x-s 签名服务地址；不发小红书可置 `None`。 |

> `sau_backend.py` 在 `conf.py` 缺失时会用 `BASE_DIR = Path(__file__).resolve().parent` 兜底并打日志；**但 `myUtils/*` 模块不会兜底**——只要缺 `BASE_DIR` 或 `LOCAL_CHROME_HEADLESS`，登录/发布/校验就起不来。所以第 3 步不要跳过。

---

## 4. 初始化 SQLite 数据库

```bash
python db/createTable.py        # 会在 db/ 下生成 database.db（已 gitignore）
```

幂等，可以重复执行。

---

## 5. 启动后端

```bash
python sau_backend.py
```

看到下面日志即为启动成功：

```
✅ 业务模块 (myUtils) 加载成功
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5409
 * Running on http://<your-lan-ip>:5409
```

打开 <http://127.0.0.1:5409> 应返回：

```
后端服务正常运行中。请直接打开 index.html 使用前端。
```

> 这是 Flask 的 `/` 路由，**不是**前端页面——前端是仓库根目录的 `index.html`，下一步打开它。

---

## 6. 打开前端

直接用浏览器打开 `index.html`：

- macOS：`open index.html`
- Linux：`xdg-open index.html`
- Windows：双击或在资源管理器里打开

前端默认请求 `http://127.0.0.1:5409`。如果后端跑在别的机器上，先编辑 `index.html` 顶部附近的 base URL 常量再打开。

如果前端能正常显示"文件管理 / 账号管理 / 视频发布"三个标签页，整条链路就通了。

---

## 7. 第一次扫码登录（验证全链路）

1. 在前端"账号管理"里选平台（如 `3` 抖音），输入账号名，点登录。
2. 前端弹出二维码。
3. 用对应平台 App 扫码。
4. 后端 Playwright 浏览器（`LOCAL_CHROME_HEADLESS=False` 时可见）会跳到平台首页。
5. 后端把 `context.storage_state()` 写到 `cookiesFile/<uuid>.json`，并向 `user_info` 表插一行。
6. 前端关闭二维码弹窗，账号列表里能看到新账号。

如果想**跳过扫码**，先验证 SSE + 前端二维码渲染链路：

```bash
# 浏览器或 curl 都可以
curl "http://127.0.0.1:5409/login?type=mock"
```

会收到一段 SSE 流，里面包含一段固定 SVG 二维码，前端弹窗能正常显示即视为链路正常。

---

## 8. 第一次发布（验证 Cookie + uploader）

1. 前端"文件管理"上传一个小视频（注意 160MB 上限）。
2. "视频发布"选刚才登录的账号、视频、标题、标签，点发布。
3. 后端先调 `validate_account_cookie()`（启动一个 headless Playwright 走平台 auth check），通过后调对应 `post_video_<platform>()` 进入实际发布流程。
4. 发布结果以账号为单位返回，单账号 Cookie 失效不会阻塞其他账号。

---

## 9. （可选）Docker 启动

仅在你需要把项目以 Docker 镜像形式部署到服务器时使用。**注意：Docker 模式下前端是 Vue 那一套，不是单文件 `index.html`**——Dockerfile 会把 Vue 产物 `dist/index.html` 覆盖到根目录。

```bash
docker build -t sau .        # 多阶段构建：先 Node 构建前端，再 Python 装依赖
docker run -p 5409:5409 sau  # 服务监听 0.0.0.0:5409
```

服务器模式下 `LOCAL_CHROME_HEADLESS=True` 是硬性要求（容器里没有显示设备）。二维码 / 短信验证各平台行为差异较大，**逐平台真实验证**后再上线。

---

## 10. （可选）Debug 模式启动

`cli_main.py` 不是 CLI，是 `sau_backend.py` 的 debug 副本（`debug=True`），改了后端代码会自动重载：

```bash
python cli_main.py           # 同 5409 端口，会和 sau_backend.py 冲突，不要同时跑
```

---

## 11. 静态语法检查

改完 `sau_backend.py` / `myUtils/*` 后，跑一下：

```bash
python -m py_compile sau_backend.py cli_main.py myUtils/login.py myUtils/auth.py myUtils/postVideo.py
```

零输出 = 通过。

---

## 常见问题

### Q: 启动报 `ModuleNotFoundError: No module named 'conf'`
没生成 `conf.py`。回到第 3 步 `cp conf.example.py conf.py`。

### Q: 启动报 `业务模块 (myUtils) 加载失败`
通常是 `conf.py` 缺变量，或依赖没装全。看日志里的具体 ImportError，对照 `conf.example.py` 补齐。

### Q: 扫码后浏览器长时间停在登录页 / 没有写入 Cookie
- 平台登录页经常改版，Playwright 选择器可能失效。需要更新 `myUtils/login.py` 里对应平台的 `*_cookie_gen()`。
- 看后端日志里有没有 `framenavigated` 事件，没收到就是等登录成功的判定条件失效。

### Q: 发布时某账号报 "Cookie 已失效"
正常路径——`validate_account_cookie()` 主动拒绝了。重新走第 7 步扫码登录即可，其他账号不受影响。

### Q: 上传视频失败 / 提示 413
视频超过 160MB。改 `sau_backend.py` 里 `MAX_CONTENT_LENGTH`，或者压一下视频。

### Q: 改了前端代码没生效
- 本地模式：你改的是单文件 `index.html`，浏览器可能要 `Ctrl+Shift+R` 强刷。
- Docker 模式：Vue 改了要重新 `docker build` 才能生效。

### Q: 想清掉所有账号重新来
```bash
rm -rf cookiesFile/*.json db/database.db
python db/createTable.py
```

---

## 速查：项目里所有可执行入口

| 入口 | 命令 | 用途 |
| --- | --- | --- |
| 主后端 | `python sau_backend.py` | 5409 端口，debug=False，**生产/本地都用它** |
| Debug 后端 | `python cli_main.py` | 5409 端口，debug=True，改代码自动重载 |
| DB 初始化 | `python db/createTable.py` | 幂等，建表 |
| SSE 冒烟测试 | `curl 'http://127.0.0.1:5409/login?type=mock'` | 不开浏览器，验 SSE + 前端 |
| 静态语法检查 | `python -m py_compile sau_backend.py cli_main.py myUtils/login.py myUtils/auth.py myUtils/postVideo.py` | 改完跑一下 |
| Docker 构建 | `docker build -t sau .` | 多阶段，会顺带构建 Vue 前端 |
| Docker 运行 | `docker run -p 5409:5409 sau` | 5409 端口，headless |