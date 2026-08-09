# social-auto-upload 快速启动 Makefile
#
# 用法:
#   make help            查看所有可用命令
#   make setup           首次运行：装依赖 + 生成 conf.py + 建表
#   make run             启动后端 (http://127.0.0.1:5409)
#   make run-debug       启动 debug 模式后端 (改代码自动重载)
#
# 包管理已切换到 pipenv。所有 Python / 浏览器驱动命令均通过 `pipenv run`
# 在 Pipfile 锁定的虚拟环境中执行，确保依赖版本一致。
#
# 配套前端: 直接用浏览器打开 index.html；前端默认连 http://127.0.0.1:5409。

.DEFAULT_GOAL := help

# 项目根目录；其他 target 复用。
ROOT_DIR := $(shell pwd)
PIPENV ?= pipenv

.PHONY: help setup install config db run run-debug smoke check \
        docker-build docker-run clean-data clean all-deps verify

# ---------------- help ----------------

help: ## 显示所有命令
	@awk 'BEGIN {FS = ":.*?## "; printf "用法: make <target>\n\n可用目标:\n"} \
	/^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' \
	$(MAKEFILE_LIST)

# ---------------- 一键初始化 ----------------

setup: install config db ## 首次运行：装依赖 + 生成 conf.py + 建表
	@echo ""
	@echo "✅ setup 完成。下一步："
	@echo "   make run           启动后端"
	@echo "   然后用浏览器打开 index.html"

# ---------------- 依赖 ----------------

install: ## 通过 pipenv 安装 Pipfile 依赖 + Chromium
	@command -v $(PIPENV) >/dev/null 2>&1 || { echo "❌ 需要 pipenv，请先 'pip install pipenv'"; exit 1; }
	$(PIPENV) install --dev
	$(PIPENV) run patchright install chromium

verify: ## 检查关键依赖能否正常导入（在 pipenv 虚拟环境内）
	@$(PIPENV) run python -c "import flask, flask_cors, patchright, requests, cv2, segno, loguru, qrcode; print('✅ 关键依赖可导入')"

# ---------------- 配置 ----------------

config: ## 从 conf.example.py 生成 conf.py（已存在则跳过）
	@if [ ! -f conf.py ]; then \
		cp conf.example.py conf.py; \
		echo "✅ 已生成 conf.py，请按需修改 BASE_DIR / LOCAL_CHROME_HEADLESS / LOCAL_CHROME_PATH / XHS_SERVER"; \
	else \
		echo "ℹ️  conf.py 已存在，跳过"; \
	fi

# ---------------- 数据库 ----------------

db: ## 初始化 SQLite 数据库（幂等）
	@mkdir -p db
	$(PIPENV) run python db/createTable.py

# ---------------- 启动 ----------------

run: ## 启动主后端（端口 5409，debug=False）
	$(PIPENV) run python sau_backend.py

run-debug: ## 启动 debug 模式后端（改代码自动重载，与 make run 互斥）
	$(PIPENV) run python cli_main.py

# ---------------- 验证 ----------------

smoke: ## SSE 登录冒烟测试（不需要扫码，验证 SSE + 前端）
	@command -v curl >/dev/null 2>&1 || { echo "❌ 需要 curl"; exit 1; }
	@if ! curl -sf http://127.0.0.1:5409/ >/dev/null; then \
		echo "❌ 后端未监听 5409，请先 'make run'"; \
		exit 1; \
	fi
	@echo "→ 请求 /login?type=mock （Ctrl+C 终止）"
	curl -N "http://127.0.0.1:5409/login?type=mock"

check: ## 静态语法检查（在 pipenv 虚拟环境内）
	$(PIPENV) run python -m py_compile sau_backend.py cli_main.py \
		myUtils/login.py myUtils/auth.py myUtils/postVideo.py
	@echo "✅ 语法 OK"

# ---------------- Docker ----------------

docker-build: ## 构建 Docker 镜像（多阶段，含 Vue 前端构建）
	docker build -t sau .

docker-run: ## 运行 Docker 容器（端口 5409）
	docker run -p 5409:5409 sau

# ---------------- 清理 ----------------

clean-data: ## 清空账号 Cookie + 数据库 + 上传视频（不可恢复）
	@echo "⚠️  即将删除 cookiesFile/*.json / db/database.db / videoFile/*"
	@read -p "确认？(y/N) " r && [ "$$r" = "y" ] || { echo "已取消"; exit 1; }
	rm -f cookiesFile/*.json
	rm -f db/database.db
	rm -f videoFile/*
	@echo "✅ 已清空。可执行 'make db' 重建表"

clean: ## 清理 Python 缓存文件（__pycache__、*.pyc）
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	@echo "✅ 缓存已清理"