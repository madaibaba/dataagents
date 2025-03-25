# -*- coding: utf-8 -*-

from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
import pandas as pd
import hashlib
from typing import Optional, List
from io import BytesIO
import numpy as np

class DataProcessor:
    """数据处理核心"""
    @staticmethod
    def clean_data(df: pd.DataFrame, sensitive_fields: List[str]) -> pd.DataFrame:
        for col in df.columns:
            if col in sensitive_fields:
                df[col] = df[col].fillna('')
                df[col] = df[col].apply(
                    lambda x: str(x)[:6] + hashlib.sha256(str(x).encode()).hexdigest()[:6]
                )

        # 空值处理优化
        numeric_cols = df.select_dtypes(include='number').columns
        if not numeric_cols.empty:
            imputer = IterativeImputer()
            df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
        
        return df
    
    @staticmethod
    def generate_report(df: pd.DataFrame) -> dict:
        """生成精简报告数据"""
        return {
            "completeness": (1 - df.isnull().mean()).to_dict(),
            "top_values": df.apply(lambda x: x.value_counts().index[0]),
            "data_shape": df.shape
        }

    @staticmethod
    def generate_report(df: pd.DataFrame) -> dict:
        """生成精简报告数据"""
        # 转换 datetime 列为 ISO 格式字符串
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        for col in datetime_cols:
            df[col] = df[col].apply(lambda x: x.isoformat() if pd.notnull(x) else None)

        # 生成 top_values 并处理 numpy 类型
        top_values = {}
        for col in df.columns:
            if not df[col].empty:
                top_val = df[col].dropna().value_counts().index[0]
                # 转换 numpy 类型为 Python 原生类型
                if isinstance(top_val, (np.integer, np.floating)):
                    top_val = top_val.item()
                top_values[col] = top_val
            else:
                top_values[col] = "N/A"

        report = {
            "completeness": (1 - df.isnull().mean()).to_dict(),
            "top_values": top_values,
            "data_shape": list(df.shape)
        }
        return report

    @staticmethod
    def generate_html_report(report_data: dict, filename: str) -> BytesIO:
        """生成交互式HTML报告"""
        import plotly.express as px
        buffer = BytesIO()
        try:
            fig = px.bar(
                x=list(report_data["completeness"].keys()),
                y=list(report_data["completeness"].values()),
                labels={"x": "字段", "y": "完整性比例"},
                title="数据完整性报告"
            )
            # 生成 HTML 字符串并显式编码为字节流
            html_content = fig.to_html(include_plotlyjs='cdn')
            buffer.write(html_content.encode('utf-8'))
            buffer.seek(0)
            return buffer
        except Exception as e:
            raise RuntimeError(f"生成HTML报告失败: {str(e)}")