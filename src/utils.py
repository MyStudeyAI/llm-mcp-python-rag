from rich.console import Console
from rich.style import Style
from rich.text import Text

console = Console()

def log_title(message: str):
    total_length = 88
    border_char = '='

    # 1. 构造完整的装饰边框字符串
    border = border_char * total_length

    # 2. 计算消息居中位置，并构造带空格的消息字符串
    padded_message = f" {message} "
    start_pos = (total_length - len(padded_message)) // 2
    
    # 创建 Text 对象并设置样式
    text = Text()
    
    # 左边框 - 绿色
    text.append(border[:start_pos], style=Style(color="green"))
    # 消息 - 亮青色
    text.append(padded_message, style=Style(color="cyan", bold=True))
    # 右边框 - 绿色
    text.append(border[start_pos + len(padded_message):], style=Style(color="green"))
    
    console.print(text)


# 使用示例
if __name__ == "__main__":
    log_title("Hello, World!")
    log_title("应用程序启动")
    log_title("数据库连接成功")