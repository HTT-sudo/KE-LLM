import os
import requests
import json
import re
import time
from typing import List, Optional
from config import API_TOKENS, INPUT_DIR_2, OUTPUT_DIR_2, PROMPT_FILE_PATH, REQUEST_METHOD


class DrugProcessor:
    def __init__(self, api_tokens: List[str], request_method: str, cooldown: int = 5):
        self.api_tokens = api_tokens
        self.current_token_index = 0
        self.request_method = request_method
        self.cooldown = cooldown
        self.last_request_time = 0

        # 确保输出目录存在
        if not os.path.exists(OUTPUT_DIR_2):
            os.makedirs(OUTPUT_DIR_2)

        # 读取完整的提示词
        with open(PROMPT_FILE_PATH, 'r', encoding='utf-8') as prompt_file:
            self.full_prompt = prompt_file.read().strip()

    def get_next_token(self) -> str:
        """获取下一个API令牌"""
        token = self.api_tokens[self.current_token_index]
        self.current_token_index = (self.current_token_index + 1) % len(self.api_tokens)
        return token

    def wait_for_cooldown(self):
        """等待冷却时间"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.cooldown:
            time.sleep(self.cooldown - elapsed)
        self.last_request_time = time.time()

    def extract_triples(self, content: str) -> List[str]:
        """从API响应中提取三元组"""
        triple_lines = []
        lines = content.split('\n')
        in_triples_section = False

        for line in lines:
            # 检测三元组部分开始
            if re.search(r'三元组[：:]', line):
                in_triples_section = True
                continue
            # 检测原文列表部分开始（三元组部分结束）
            elif re.search(r'原文列表[：:]', line):
                break

            # 如果在三元组部分且行不为空，提取三元组
            if in_triples_section and line.strip():
                # 匹配三元组格式 (实体1, 关系, 实体2)
                if re.match(r'\([^,]+,\s*[^,]+,\s*[^)]+\)', line.strip()):
                    triple_lines.append(line.strip())

        # 如果没有找到明确的三元组部分，尝试匹配所有可能的三元组行
        if not triple_lines:
            for line in lines:
                if re.match(r'\([^,]+,\s*[^,]+,\s*[^)]+\)', line.strip()):
                    triple_lines.append(line.strip())

        return triple_lines

    def make_api_request(self, content: str, max_retries: int = 3) -> Optional[str]:
        """向DeepSeek API发送请求，支持重试"""
        for attempt in range(max_retries):
            try:
                self.wait_for_cooldown()
                current_token = self.get_next_token()

                # 只保留DeepSeek API调用
                from openai import OpenAI

                # 使用DeepSeek官方API端点
                client = OpenAI(api_key=current_token, base_url="https://api.deepseek.com")

                response = client.chat.completions.create(
                    model="deepseek-reasoner",  # 使用正确的模型名称
                    messages=[{"role": "user", "content": content}],
                    stream=False,
                    temperature=0.3,
                    max_tokens=8192,
                    top_p=0.9
                )

                return response.choices[0].message.content

            except Exception as e:
                print(f"API请求错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")

            # 最后一次尝试不等待直接返回
            if attempt < max_retries - 1:
                print(f"等待 {self.cooldown} 秒后重试...")
                time.sleep(self.cooldown)

        return None

    def process_file(self, file_path: str, filename: str):
        """处理单个文件"""
        with open(file_path, 'r', encoding='utf-8') as file:
            drug_description = file.read().strip()

        print(f"\n处理药物描述文件: {filename}")
        print(f"药物描述内容: {drug_description[:100]}...")

        # 组合提示词和药物描述
        content = self.full_prompt + "\n\n请根据我提供的实体、关系、示例，并以三元组的形式存储为txt格式进行输出来处理以下输入：\n\n药物描述文本:\n" + drug_description

        # 发送API请求
        response_content = self.make_api_request(content)

        if response_content is None:
            print(f"处理文件 {filename} 失败，跳过")
            return

        # 提取三元组
        triple_lines = self.extract_triples(response_content)

        # 保存结果
        output_file_path = os.path.join(OUTPUT_DIR_2, f"{os.path.splitext(filename)[0]}.txt")

        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            if triple_lines:
                output_file.write("三元组：\n")
                for triple in triple_lines:
                    output_file.write(triple + "\n")
            else:
                output_file.write("未提取到三元组\n")

            output_file.write("\n原文列表：\n")
            output_file.write(drug_description)

        print(f"成功保存 {len(triple_lines)} 个三元组到 {output_file_path}")

    def process_all_files(self):
        """处理所有文件"""
        files = [f for f in os.listdir(INPUT_DIR_2)
                 if os.path.isfile(os.path.join(INPUT_DIR_2, f)) and f.endswith('.txt')]

        print(f"找到 {len(files)} 个待处理文件")

        for i, filename in enumerate(files):
            print(f"\n处理进度: {i + 1}/{len(files)}")
            file_path = os.path.join(INPUT_DIR_2, filename)
            self.process_file(file_path, filename)

        print("\n所有文件处理完成")


# 主程序
if __name__ == "__main__":
    # 确保API_TOKENS是列表格式
    if isinstance(API_TOKENS, str):
        api_tokens = [API_TOKENS]
    else:
        api_tokens = API_TOKENS

    processor = DrugProcessor(api_tokens, REQUEST_METHOD)
    processor.process_all_files()