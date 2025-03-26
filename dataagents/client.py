# -*- coding: utf-8 -*-

import uuid
from datetime import datetime
import json
from typing import Dict, Any
from .core.storage import StorageManager
from .core.agents import AgentSystem
from .core.processing import DataProcessor
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
import logging

logger = logging.getLogger("dataagents")
logger.setLevel(logging.INFO)

class DataGovernanceClient:
    """用户友好接口"""
    def __init__(self, 
                 minio_endpoint: str,
                 minio_access: str,
                 minio_secret: str,
                 ollama_config: Dict,
                 bucket: str,
                 base_path: str):
        self.bucket = bucket
        self.base_path = base_path
        self.storage = StorageManager(minio_endpoint, minio_access, minio_secret)
        self.storage._ensure_bucket(bucket)
        self.agent_system = AgentSystem(
            llm_config={
                "config_list": [{
                    "model": ollama_config["model"],
                    "base_url": ollama_config["base_url"],
                    "api_key": "NULL",
                    "price": [0.0, 0.0]
                }],
                "timeout": 300
            }
        )

    def process_file(self, 
                    input_filename: str,
                    sensitive_fields: List[str],
                    full_path: Optional[str] = None) -> Dict[str, Any]:
        """端到端处理流程"""
        process_id = f"{self.base_path}-{uuid.uuid4()}"
        try:
            # 构建路径
            if full_path is None:
                raw_path = self.storage.build_object_path(
                    f"{self.base_path}/raw", input_filename
                )
            else:
                raw_path = full_path
            processed_path = self.storage.build_object_path(
                f"{self.base_path}/processed", input_filename
            )

            # 启动智能体流程
            manager = self.agent_system.get_chat_manager()
            self.agent_system.agents[0].initiate_chat(
                manager,
                message=f"""
                开始处理文件：{raw_path}
                处理要求：
                1. 敏感字段：{', '.join(sensitive_fields)}
                2. 输出格式：原文件格式
                3. 质量验证级别：严格
                """
            )
            
            # 执行实际处理
            df = self.storage.load_dataframe(self.bucket, raw_path)
            cleaned_df = DataProcessor.clean_data(df, sensitive_fields)
            self.storage.save_dataframe(cleaned_df, self.bucket, processed_path)
            
            # 生成报告数据
            report_data = DataProcessor.generate_report(cleaned_df)
            
            # 生成HTML报告并保存到MinIO
            html_buffer = DataProcessor.generate_html_report(report_data, "report.html")
            report_path = self.storage.build_object_path(
                f"{self.base_path}/report", f"{input_filename}_report.html"
            )
            self.storage.client.put_object(
                self.bucket,
                report_path,
                html_buffer,
                length=len(html_buffer.getvalue())
            )

            return {
                "status": "success",
                "processed_path": processed_path,
                "report": report_data,
                "report_path": report_path  # 返回报告路径用于日志
            }
        except Exception as e:
            self._log_error(process_id, str(e))
            return {"status": "error", "message": str(e)}

    def _log_error(self, process_id: str, error: str):
        """统一错误日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "process_id": process_id,
            "error": error
        }
        log_path = self.storage.build_object_path(
            f"{self.base_path}/logs", f"errors/{process_id}.json"
        )
        self.storage.client.put_object(
            self.bucket,
            log_path,
            BytesIO(json.dumps(log_entry).encode()),
            len(json.dumps(log_entry))
        )

    def process_directory(self, 
                         sensitive_fields: List[str],
                         max_workers: int = 4) -> Dict[str, Any]:
        """处理目录下所有文件"""
        process_id = f"batch-{uuid.uuid4()}"
        results = {
            "status": "started",
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "details": {}
        }
        
        try:
            # 获取文件列表
            files = self.storage.list_directory(
                self.bucket, 
                f"{self.base_path}/raw"
            )
            if not files:
                raise ValueError("目录中没有可处理文件")
            
            # 并行处理
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        self._safe_process_file,
                        file_path=file,
                        sensitive_fields=sensitive_fields
                    ): file for file in files
                }
                
                for future in as_completed(futures):
                    file_path = futures[future]
                    try:
                        result = future.result()
                        results["details"][file_path] = result
                        results["succeeded"] += 1
                    except Exception as e:
                        results["details"][file_path] = {"error": str(e)}
                        results["failed"] += 1
                    finally:
                        results["processed"] += 1
            
            results["status"] = "completed"
            return results
            
        except Exception as e:
            self._log_error(process_id, f"批量处理失败: {str(e)}")
            results.update({
                "status": "error",
                "message": str(e)
            })
            return results

    def _safe_process_file(self, file_path: str, sensitive_fields: List[str]):
        """带异常捕获的文件处理"""
        try:
            # 提取文件名
            filename = file_path.split('/')[-1]
            
            # 处理单个文件
            return self.process_file(
                input_filename=filename,
                sensitive_fields=sensitive_fields,
                full_path=file_path  # 新增参数
            )
        except Exception as e:
            raise RuntimeError(f"文件处理失败: {file_path} - {str(e)}")
