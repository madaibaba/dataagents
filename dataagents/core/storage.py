# -*- coding: utf-8 -*-

from minio import Minio
from minio.error import S3Error
from io import BytesIO
import pandas as pd
from typing import Optional, List

class StorageManager:
    """统一存储管理"""
    def __init__(self, endpoint: str, access_key: str, secret_key: str):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
       
    def _ensure_bucket(self, bucket: str):
        try:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
        except S3Error as e:
            raise RuntimeError(f"存储桶初始化失败: {e.message}")
    
    def build_object_path(self, base_path: str, filename: str) -> str:
        return f"{base_path.rstrip('/')}/{filename.lstrip('/')}"
    
    def load_dataframe(self, bucket: str, object_path: str) -> pd.DataFrame:
        response = self.client.get_object(bucket, object_path)
        if object_path.endswith('.parquet'):
            return pd.read_parquet(BytesIO(response.data))
        elif object_path.endswith('.json'):
            return pd.read_json(BytesIO(response.data))
        elif object_path.endswith('.jsonl'):
            return pd.read_json(BytesIO(response.data), lines=True)
        elif object_path.endswith('.csv'):
            return pd.read_csv(BytesIO(response.data))
        else:
            raise ValueError(f"Unsupported file format: {object_path}")

    def save_dataframe(self, df: pd.DataFrame, bucket: str, object_path: str):
        """保存处理结果"""
        buffer = BytesIO()
        if object_path.endswith('.parquet'):
            df.to_parquet(buffer)
        elif object_path.endswith('.json'):
            df.to_json(buffer, orient="records")
        elif object_path.endswith('.jsonl'):
            df.to_json(buffer, orient="records", lines=True)
        elif object_path.endswith('.csv'):
            df.to_csv(buffer, index=False)
        else:
            raise ValueError(f"Unsupported save format: {object_path}")
        buffer.seek(0)
        self.client.put_object(
            bucket,
            object_path,
            buffer,
            length=buffer.getbuffer().nbytes
        )

    def list_directory(self, bucket: str, prefix: str) -> List[str]:
        """列出目录下的所有文件"""
        try:
            objects = self.client.list_objects(
                bucket_name=bucket,
                prefix=prefix.rstrip('/') + '/',
                recursive=False
            )
            return [obj.object_name for obj in objects if not obj.is_dir]
        except S3Error as e:
            raise RuntimeError(f"目录列表失败: {e.message}")