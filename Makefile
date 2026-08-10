# social-auto-upload 快速启动 Makefile
#
# 用法:
#   make help            查看所有可用命令
#   make setup           首次运行：装 v1+v2 依赖 + 生成 conf.py + 建表
#   make run             启动旧版 Web 后端 (http://127.0.0.1:5409)
#   make v2-backend      启动新版 FastAPI 后端 (http://127.0.0.1:6409)
#   make v2-frontend     启动新版 React 前端 (http://127.0.0.1:6173)
#   make v2-dev          同启 v2 后端 + 前端
#
# 主流程已切换到 v2（sau_backend_v2/ + sau_frontend_v2/）。旧版（sau_backend.py +
# index.html / sau_frontend/）保留为参考，命令仍在 v1-* 前缀下可用。
#
# 配套前端默认连 http://127.0.0.1:6409/api，前端 dev server 用 Vite proxy 转发。

.DEFAULT_GOAL := help

# 项目根目录；其他 target 复用。
ROOT_DIR := $(shell pwd)
UV       ?= uv
PIPENV   ?= pipenv
PNPM     ?= pnpm
PYTHON   ?= python
NODE     ?= node

.PHONY: help setup install config db run run-debug smoke check \
        v1-run v1-run-debug v1-smoke v1-check \
        v2-install v2-backend v2-backend-debug v2-frontend-install \
        v2-frontend v2-frontend-build v2-dev v2-stop v2-check \
        docker-build docker-run clean-data clean all-deps verify

# ---------------- help ----------------

help: ## 显示所有命令
	@awk 'BEGIN {FS = ":.*?## "; printf "用法: make <target>\n\n可用目标:\n"} \
	/^[a-zA-Z0-9_-]+:.*?## / {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' \
	$(MAKEFILE_LIST)

# ---------------- 一键初始化 ----------------

setup: install config db v2-install v2-frontend-install ## 首次运行：装 v1+v2 依赖 + 生成 conf.py + 建表
	@echo ""
	@echo "✅ setup 完成。下一步："
	@echo "   make v2-dev      启动 v2 后端 + 前端（推荐）"
	@echo "   make v2-backend  仅启动 FastAPI (127.0.0.1:6409)"
	@echo "   make run         启动旧版 Web 后端（参考用）"

# ---------------- 依赖 ----------------

install: ## 通过 uv 安装 pyproject.toml 依赖 + Chromium
	@command -v $(UV) >/dev/null 2>&1 || { echo "❌ 需要 uv，请先 'pip install uv'"; exit 1; }
	$(UV) venv
	$(UV) pip install -e ".[v2]"
	$(UV) run patchright install chromium

verify: ## 检查关键依赖能否正常导入（在当前虚拟环境内）
	@$(PYTHON) -c "import fastapi, uvicorn, pydantic, multipart, patchright, requests, cv2, segno, loguru, qrcode; print('✅ 关键依赖可导入')"

# ---------------- 配置 ----------------

config: ## 从 conf.example.py 生成 conf.py（已存在则跳过）
	@if [ ! -f conf.py ]; then \
		cp conf.example.py conf.py; \
		echo "✅ 已生成 conf.py，请按需修改 BASE_DIR / LOCAL_CHROME_HEADLESS / LOCAL_CHROME_PATH / XHS_SERVER"; \
	else \
		echo "ℹ️  conf.py 已存在，跳过"; \
	fi

# ---------------- 数据库 ----------------

db: ## 初始化 SQLite 数据库（幂等；v2 后端启动时也会自动跑 migration）
	@mkdir -p db
	$(PYTHON) db/createTable.py

# ---------------- v1 旧 Web 后端（参考用，不推荐） ----------------

run: ## [v1] 启动旧版 Web 后端（端口 5409，debug=False）
	$(PYTHON) sau_backend.py

run-debug: ## [v1] 启动 debug 模式旧版后端（已移除 cli_main.py，会失败）
	@echo "⚠️  cli_main.py 已被移除。改用 'make v2-backend-debug'。"
	@exit 1

v1-run: run ## [v1] 同 make run
v1-run-debug: run-debug ## [v1] 同 make run-debug

# ---------------- v2 后端（FastAPI，推荐） ----------------

v2-install: ## [v2] 安装 FastAPI / uvicorn / pydantic / python-multipart
	@command -v $(UV) >/dev/null 2>&1 || { echo "❌ 需要 uv，请先 'pip install uv'"; exit 1; }
	$(UV) pip install -e ".[v2]"

v2-backend: ## [v2] 启动 FastAPI 后端 (http://127.0.0.1:6409, debug 关闭)
	@command -v $(UV) >/dev/null 2>&1 || { echo "❌ 需要 uv"; exit 1; }
	$(UV) run uvicorn sau_backend_v2.main:app --host 127.0.0.1 --port 6409

v2-backend-debug: ## [v2] 启动 FastAPI 后端 (改代码自动重载, http://127.0.0.1:6409)
	@command -v $(UV) >/dev/null 2>&1 || { echo "❌ 需要 uv"; exit 1; }
	$(UV) run uvicorn sau_backend_v2.main:app --host 127.0.0.1 --port 6409 --reload

# ---------------- v2 前端（React + Vite） ----------------

v2-frontend-install: ## [v2] 安装 React + Vite 依赖（pnpm install）
	@command -v $(PNPM) >/dev/null 2>&1 || { echo "❌ 需要 pnpm，请先 'npm install -g pnpm'"; exit 1; }
	cd sau_frontend_v2 && $(PNPM) install

v2-frontend: ## [v2] 启动 Vite dev server (http://127.0.0.1:6173)
	@command -v $(PNPM) >/dev/null 2>&1 || { echo "❌ 需要 pnpm"; exit 1; }
	cd sau_frontend_v2 && $(PNPM) dev

v2-frontend-build: ## [v2] 构建生产包到 sau_frontend_v2/dist/
	cd sau_frontend_v2 && $(PNPM) build

# ---------------- v2 联调（同启后端 + 前端） ----------------

v2-dev: ## [v2] 同启 FastAPI 后端 + Vite 前端（前端会通过 proxy 调后端）
	@command -v $(PNPM) >/dev/null 2>&1 || { echo "❌ 需要 pnpm"; exit 1; }
	@command -v $(UV) >/dev/null 2>&1 || { echo "❌ 需要 uv"; exit 1; }
	@mkdir -p logs/v2
	@echo "→ 启动后端 (uvicorn) + 前端 (vite)，日志: logs/v2/dev-backend.log / logs/v2/dev-frontend.log"
	@echo "→ 停止: make v2-stop"
	@$(UV) run uvicorn sau_backend_v2.main:app --host 127.0.0.1 --port 6409 > logs/v2/dev-backend.log 2>&1 & echo $$! > logs/v2/dev-backend.pid
	# `cd` 后面的 `..` 在外层 make 子 shell 里会解析成 <项目父目录>/...,所以两条命令的路径都用绝对路径(基于 $(ROOT_DIR))
	@cd sau_frontend_v2 && $(PNPM) dev > $(ROOT_DIR)/logs/v2/dev-frontend.log 2>&1 & echo $$! > $(ROOT_DIR)/logs/v2/dev-frontend.pid
	@echo "✅ 后端 PID: $$(cat logs/v2/dev-backend.pid)  前端 PID: $$(cat logs/v2/dev-frontend.pid)"
	@echo "   后端: http://127.0.0.1:6409/docs"
	@echo "   前端: http://127.0.0.1:6173"

v2-stop: ## [v2] 停止 v2-dev 拉起的后端 + 前端
	@if [ -f logs/v2/dev-backend.pid ]; then \
		kill $$(cat logs/v2/dev-backend.pid) 2>/dev/null && echo "✅ 后端已停止" || echo "ℹ️  后端已退出"; \
		rm -f logs/v2/dev-backend.pid; \
	fi
	@if [ -f logs/v2/dev-frontend.pid ]; then \
		kill $$(cat logs/v2/dev-frontend.pid) 2>/dev/null && echo "✅ 前端已停止" || echo "ℹ️  前端已退出"; \
		rm -f logs/v2/dev-frontend.pid; \
	fi

# ---------------- 验证（跨 v1/v2） ----------------

v2-check: ## [v2] TypeScript 类型检查 + Python 语法检查
	cd sau_frontend_v2 && $(PNPM) exec tsc --noEmit
	$(PYTHON) -m py_compile sau_backend_v2/main.py \
		sau_backend_v2/routers/*.py \
		sau_backend_v2/services/*.py \
		sau_backend_v2/models/*.py
	@echo "✅ v2 类型 + 语法 OK"

smoke: v1-smoke ## [v1] 同 make v1-smoke

v1-smoke: ## [v1] SSE 登录冒烟测试（不需要扫码，验证旧版 SSE）
	@command -v curl >/dev/null 2>&1 || { echo "❌ 需要 curl"; exit 1; }
	@if ! curl -sf http://127.0.0.1:5409/ >/dev/null; then \
		echo "❌ 旧版后端未监听 5409，请先 'make run' 或改用 v2: 'make v2-backend'"; \
		exit 1; \
	fi
	@echo "→ 请求 /login?type=mock （Ctrl+C 终止）"
	curl -N "http://127.0.0.1:5409/login?type=mock"

v2-smoke: ## [v2] 健康检查 + auth 端点验证
	@command -v curl >/dev/null 2>&1 || { echo "❌ 需要 curl"; exit 1; }
	@if ! curl -sf http://127.0.0.1:6409/healthz >/dev/null; then \
		echo "❌ v2 后端未监听 6409，请先 'make v2-backend'"; \
		exit 1; \
	fi
	@echo "→ /healthz"; curl -sS http://127.0.0.1:6409/healthz
	@echo ""
	@echo "→ /api/auth/login (admin/admin)"; curl -sS -X POST http://127.0.0.1:6409/api/auth/login \
		-H "Content-Type: application/json" -d '{"username":"admin","password":"admin"}'

check: v1-check ## [v1] 同 make v1-check

v1-check: ## [v1] 旧版文件静态语法检查
	$(PYTHON) -m py_compile sau_backend.py myUtils/login.py myUtils/auth.py myUtils/postVideo.py
	@echo "✅ v1 语法 OK"

# ---------------- Docker ----------------

docker-build: ## 构建 Docker 镜像（多阶段，含 Vue 旧前端构建）
	docker build -t sau .

docker-run: ## 运行 Docker 容器（端口 5409）
	docker run -p 5409:5409 sau

# ---------------- 清理 ----------------

clean-data: ## 清空账号 Cookie + 数据库 + 上传视频（不可恢复）
	@echo "⚠️  即将删除 cookiesFile/*.json / cookies/*.json / db/database.db / videoFile/ / videos/*_e2e*"
	@read -p "确认？(y/N) " r && [ "$$r" = "y" ] || { echo "已取消"; exit 1; }
	rm -f cookiesFile/*.json
	rm -f cookies/*.json
	rm -f db/database.db
	rm -f videoFile/*
	find videos -maxdepth 1 -name '*_e2e*' -delete
	@echo "✅ 已清空。可执行 'make db' 重建表"

clean: ## 清理 Python 缓存文件（__pycache__、*.pyc）
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	@echo "✅ 缓存已清理"
