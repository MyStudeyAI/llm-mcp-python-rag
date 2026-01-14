# 步骤1：安装uv（如果尚未安装）
```bash
pip install uv
```
或者参考uv的官方安装指南。

# 步骤2：使用uv创建虚拟环境并安装FastAPI和uvicorn
```bash
uv venv  # 创建虚拟环境
# 激活虚拟环境（根据你的操作系统）
# 在Windows上：
# .venv\Scripts\activate
# 在Unix或MacOS上：
# source .venv/bin/activate

# 使用uv安装依赖
uv add -r requirements.txt
```
