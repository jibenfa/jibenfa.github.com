import os
import re

def replace_pre_code_with_fenced_code(md_folder):
    # 匹配 <pre><code class="language-xxx"> ... </code></pre>
    # 允许class里还有其他类名，且内容跨多行
    pattern = re.compile(
        r'<pre><code\s+class="language-([a-zA-Z0-9_-]+)">([\s\S]*?)</code></pre>',
        re.MULTILINE
    )

    for root, _, files in os.walk(md_folder):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                def repl(match):
                    lang = match.group(1)
                    code = match.group(2)
                    # 反转义html实体，确保代码里是正常字符
                    code = code.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                    # 保留原缩进和换行
                    return f'```{lang}\n{code}\n```'

                new_content = pattern.sub(repl, content)

                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f'Processed {file_path}')

if __name__ == "__main__":
    folder_path = '.\\_posts'  # 修改为你的目录
    replace_pre_code_with_fenced_code(folder_path)
