import os
import gradio as gr
from datetime import datetime
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from main import main  # 复用原有的main函数

# 读取formatter prompt
with open("prompts/formatter.txt", "r", encoding="utf-8") as f:
    FORMATTER_PROMPT = f.read()

# 配置LangChain
model = ChatOpenAI(model="gpt-4o-mini")
prompt = ChatPromptTemplate.from_template(FORMATTER_PROMPT + "\n{text}")
chain = prompt | model | StrOutputParser()


def chat_and_format(text, history):
    """处理用户输入：更新对话并转换为md"""
    # 生成markdown内容
    md_content = chain.invoke({"text": text})

    # 生成文件名（使用时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"inputs/chat_{timestamp}.md"

    # 保存markdown文件
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 更新对话历史和下拉框，并清空输入框
    return (
        "",  # 清空输入框
        history + [(text, "已将输入内容转为md格式文件")],  # 更新对话历史
        gr.Dropdown(choices=get_md_files(), value=filename)  # 更新下拉框
    )


def get_md_files():
    """获取inputs目录下的所有md文件"""
    return [
        os.path.join("inputs", file)
        for file in os.listdir("inputs")
        if file.endswith(".md")
    ]


def generate_ppt(md_file):
    """生成PPT并返回文件路径"""
    if not md_file:
        return "请先选择一个markdown文件"

    # 调用原有的main函数生成PPT
    main(md_file)

    # 获取生成的PPT文件路径
    with open(md_file, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
        title = first_line.replace("#", "").strip()
    return f"outputs/{title}.pptx"


# 创建Gradio界面
with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="输入")

    with gr.Row():
        md_dropdown = gr.Dropdown(
            choices=get_md_files(),
            label="选择md文件",
            interactive=True,
            value=None
        )
        generate_btn = gr.Button("由md文件生成PPT")

    output = gr.File(label="生成的PPT")

    # 更新下拉框选项
    def refresh_dropdown(selected_value):
        files = get_md_files()
        if selected_value in files:
            return gr.Dropdown(choices=files, value=selected_value)
        return gr.Dropdown(choices=files, value=None)

    # 绑定事件
    msg.submit(chat_and_format, inputs=[msg, chatbot], outputs=[msg, chatbot, md_dropdown])
    md_dropdown.change(refresh_dropdown, inputs=[md_dropdown], outputs=[md_dropdown])
    generate_btn.click(generate_ppt, inputs=[md_dropdown], outputs=[output])

if __name__ == "__main__":
    demo.launch()
