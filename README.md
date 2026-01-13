# 步骤1：安装uv（如果尚未安装）
```bash
pip install uv
```
或者参考uv的官方安装指南。

# 步骤2：创建项目目录
```bash
mkdir my-fastapi-app
cd my-fastapi-app
```

# 步骤3：使用uv创建虚拟环境并安装FastAPI和uvicorn
```bash
uv venv  # 创建虚拟环境
# 激活虚拟环境（根据你的操作系统）
# 在Windows上：
# .venv\Scripts\activate
# 在Unix或MacOS上：
# source .venv/bin/activate

# 使用uv安装FastAPI和uvicorn
uv add fastapi uvicorn[standard]
```
或者，你也可以不激活虚拟环境，而使用uv run来运行命令，但激活虚拟环境更方便。

# 步骤4：创建FastAPI应用
创建一个`main.py`文件，内容如下：

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
```

# 步骤5：运行应用
使用uvicorn运行FastAPI应用：

```bash
uvicorn main:app --reload
```
现在，你的应用应该运行在http://127.0.0.1:8000。

# 步骤6：添加其他依赖
你可以使用uv add命令添加其他依赖，例如：

```
bash
uv add requests
```

# 步骤7：创建requirements.txt（可选）
如果你想要一个requirements.txt文件，可以使用以下命令生成：

```bash
uv pip freeze > requirements.txt
```

# 使用模板
如果你希望使用一个现有的模板（比如一个GitHub模板），你可以直接使用该模板创建仓库。例如，你可以访问GitHub上的fastapi模板或者搜索其他FastAPI模板。