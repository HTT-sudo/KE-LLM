# config.py

# Define the API token as a public variable
# deepseek
# API_TOKEN = "sk-4432586b3896450982cda11fbeb92e38"  # Replace with your actual token sk-wocydnnljcxjsdjgjkeixhcfonckpkxzzummkziogwxlzamb

# # deepseek
# API_TOKENS = ["sk-f07249f1e5de4e48807eca7e35673483", "sk-0162a395ff06496e98b7b7fa8fdbba92", "sk-2339926b935b4c46bad0519ac67a25fc",
#               "sk-28754b0bfa554455b975020a4da2cff3", "sk-f41beeb55fdb40c799f6ae61ab92e9dd", "sk-f1f0debc16664549bc90ce7a65d6f8e6",
#               "sk-2fb442df104042c0bef4b1dcd743f321", "sk-35c337a5ae8641cea1478937b392ae0a", "sk-122770ef7e1a4351a0ffcbd6e382d06b",
#               "sk-12f32da67c2a4163ac9111bf5015b18e"]

# # 豆包
# API_TOKENS =["9d9c4b8f-2715-4130-a5aa-5578a6bfd93b", "5032f75f-b1d9-484d-912a-cc0c5a467f82", "b09f591a-b218-4091-b5c2-5e767033a2b1",
#              "f71f4806-4599-4f66-b9f0-aa9848180dee", "52c99478-fb70-41ab-894c-c7203edb8011", "bcfa0a96-35ee-42a5-a006-c4710c279417",
#              "91987003-75de-4b22-87f2-d718450a9b73", "49e830f1-ba61-4c89-9acd-ddefd50ec6ff", "9d38f815-7d56-4603-8c66-84a81a77cc22",
#              "87f4b383-db51-4eb0-bec6-b4419d1acde8"]

# 千问
API_TOKENS = ["sk-7588339a6bcf4c95ab47fe74273a8bcf", "sk-d46b95910202422d8ee475ea5a98e47f", "sk-99717a56336e4e7b89b8ffe4fad5e16e",
              "sk-44b7527e2f40454b89772dea6408bcb6", "sk-52b580e15dde44bd9522b24c549e523f", "sk-af9cc5b9d6d04ba5a8922be4201239fe",
              "sk-0be20d8b906d466ca57aed6df91276f6", "sk-a5a671f14745437dbe08048bd0ed89c1", "sk-8a766a1ddcae4c728664d4779e6dc479",
              "sk-01f38370f5ab4af0b1577c7446878bca"]

# Define paths for input directory, output directory, and prompt file
INPUT_DIR = 'step1/test'
OUTPUT_DIR = 'step2/deepseek'

INPUT_DIR_2 = 'step1/test'
OUTPUT_DIR_2 = 'step2/test-qianwen'

PROMPT_FILE_PATH = 'prompt.txt'

# Define the request method: 'siliconflow' or 'deepseek'
REQUEST_METHOD = 'qwen3-max-preview'  # Change to 'deepseek' to use DeepSeek API  siliconflow
# REQUEST_METHOD = 'qwen3-max-preview'