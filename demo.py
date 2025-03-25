# -*- coding: utf-8 -*-

from dataagents import DataGovernanceClient
import json

client = DataGovernanceClient(
    minio_endpoint="your-minio-endpoint:9000",
    minio_access="your-access-key",
    minio_secret="your-secret-key",
    ollama_config={
        "model": "your-llm-model",
        "base_url": "http://your-llm-api-url/v1",
        "api_key": "your-api-key" 
    },
    bucket="your-bucket-name",
    base_path="your-project-path"
)

result = client.process_directory(
    input_prefix="raw", 
    sensitive_fields=["name"],
    max_workers=4
)

print(f"""
批量处理结果：
总文件数：{result['processed']}
成功：{result['succeeded']}
失败：{result['failed']}
详细报告：{json.dumps(result['details'], indent=2)}
""")