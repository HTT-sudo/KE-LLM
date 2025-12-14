import os
import requests
import json
import re
import time
import socket
from typing import List, Optional
from config import API_TOKENS, INPUT_DIR_2, OUTPUT_DIR_2, PROMPT_FILE_PATH, REQUEST_METHOD
from openai import OpenAI


class DrugProcessor:
    def __init__(self, api_tokens: List[str], request_method: str, cooldown: int = 5):
        self.api_tokens = api_tokens
        self.current_token_index = 0
        self.request_method = request_method
        self.cooldown = cooldown
        self.last_request_time = 0
        self.failed_tokens = set()  # 记录失败的token
        self.client = None  # 初始化OpenAI客户端

        # 确保输出目录存在
        if not os.path.exists(OUTPUT_DIR_2):
            os.makedirs(OUTPUT_DIR_2)

        # 读取完整的提示词
        with open(PROMPT_FILE_PATH, 'r', encoding='utf-8') as prompt_file:
            self.full_prompt = prompt_file.read().strip()

    def get_next_token(self) -> Optional[str]:
        """获取下一个有效的API令牌"""
        if len(self.failed_tokens) >= len(self.api_tokens):
            print("所有API令牌都已失败，无法继续处理")
            return None

        token = self.api_tokens[self.current_token_index]
        self.current_token_index = (self.current_token_index + 1) % len(self.api_tokens)

        # 如果这个token之前失败过，尝试下一个
        if token in self.failed_tokens:
            return self.get_next_token()

        return token

    def mark_token_failed(self, token: str):
        """标记一个token为失败"""
        self.failed_tokens.add(token)
        print(f"标记token {token[:10]}... 为失败")

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

    def test_connection(self, endpoint: str) -> bool:
        """测试到特定端点的连接"""
        try:
            # 只测试基本连接，不发送完整请求
            response = requests.get(endpoint.replace("/api/v3/chat/completions", ""), timeout=10)
            return response.status_code < 500  # 5xx错误表示服务器问题
        except:
            return False

    def initialize_openai_client(self, token: str) -> Optional[OpenAI]:
        """初始化OpenAI客户端"""
        endpoints = [
            "https://ark.cn-beijing.volces.com/api/v3"
        ]

        # 测试连接，选择可用的端点
        available_endpoints = []
        for endpoint in endpoints:
            if self.test_connection(endpoint):
                available_endpoints.append(endpoint)
                print(f"端点 {endpoint} 可用")
            else:
                print(f"端点 {endpoint} 不可用")

        if not available_endpoints:
            print("所有端点都不可用")
            return None

        # 使用第一个可用的端点
        endpoint = available_endpoints[0]
        print(f"使用端点: {endpoint}")

        try:
            client = OpenAI(
                base_url=endpoint,
                api_key=token
            )
            return client
        except Exception as e:
            print(f"初始化OpenAI客户端失败: {str(e)}")
            return None

    def make_api_request(self, content: str, max_retries: int = 3) -> Optional[str]:
        """向API发送请求，支持重试"""
        for attempt in range(max_retries):
            try:
                self.wait_for_cooldown()
                current_token = self.get_next_token()

                if current_token is None:
                    print("没有可用的有效API令牌")
                    return None

                if self.request_method == 'doubao':
                    # 使用OpenAI客户端发送请求
                    client = self.initialize_openai_client(current_token)
                    if client is None:
                        print("无法初始化OpenAI客户端")
                        return None

                    response = client.chat.completions.create(
                        model="doubao-seed-1-6-thinking-250715",  # 您的推理接入点ID
                        messages=[{"role": "user", "content": content}],
                        stream=False,
                        max_tokens=4096,
                        temperature=0.3,
                        top_p=0.9
                    )

                    # 返回回复内容
                    return response.choices[0].message.content

                else:
                    print(f"不支持的请求方法: {self.request_method}")
                    return None

            except Exception as e:
                print(f"API请求错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                # 增加等待时间
                time.sleep(self.cooldown * (attempt + 1))

                # 如果是认证错误，标记token为失败
                if "401" in str(e) or "403" in str(e) or "authentication" in str(e).lower():
                    self.mark_token_failed(current_token)

            # 最后一次尝试不等待直接返回
            if attempt < max_retries - 1:
                print(f"等待 {self.cooldown * (attempt + 1)} 秒后重试...")
                time.sleep(self.cooldown * (attempt + 1))

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
                # 如果未提取到三元组，可以记录原始响应以便调试
                with open(os.path.join(OUTPUT_DIR_2, f"{os.path.splitext(filename)[0]}_response.txt"), 'w',
                          encoding='utf-8') as resp_file:
                    resp_file.write(response_content)

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

    # 验证API令牌
    print("验证API令牌...")
    valid_tokens = []
    for token in api_tokens:
        if token and token.strip():
            valid_tokens.append(token.strip())

    if not valid_tokens:
        print("错误: 没有提供有效的API令牌")
        exit(1)

    print(f"使用 {len(valid_tokens)} 个API令牌")

    # 测试网络连接
    print("\n测试网络连接...")
    test_endpoints = [
        "https://ark.cn-beijing.volces.com",
        "https://www.baidu.com"  # 测试基本网络连接
    ]

    for endpoint in test_endpoints:
        try:
            response = requests.get(endpoint, timeout=10)
            print(f"成功连接到 {endpoint} (状态码: {response.status_code})")
        except Exception as e:
            print(f"无法连接到 {endpoint}: {str(e)}")

    processor = DrugProcessor(valid_tokens, REQUEST_METHOD)
    processor.process_all_files()