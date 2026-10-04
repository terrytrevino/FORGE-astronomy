import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import boto3


@dataclass
class StorageConfig:
    backend: str = "local"
    bucket: Optional[str] = None
    prefix: str = "forge"
    endpoint_url: Optional[str] = None
    region_name: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None


class Storage:
    def __init__(self, config: StorageConfig):
        self.config = config
        self.backend = config.backend

        if self.backend == "local":
            self.root = Path("webapp_storage")
            self.root.mkdir(parents=True, exist_ok=True)
            self.client = None
        elif self.backend == "s3":
            if not config.bucket:
                raise ValueError("S3 bucket is required")
            self.client = boto3.client(
                "s3",
                endpoint_url=config.endpoint_url or None,
                region_name=config.region_name or None,
                aws_access_key_id=config.aws_access_key_id or None,
                aws_secret_access_key=config.aws_secret_access_key or None,
            )
        else:
            raise ValueError(f"Unsupported storage backend: {self.backend}")

    def _key(self, key: str) -> str:
        key = key.lstrip("/")
        prefix = (self.config.prefix or "").strip("/")
        return f"{prefix}/{key}" if prefix else key

    def save_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream"):
        if self.backend == "local":
            path = self.root / self._key(key)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return str(path)

        object_key = self._key(key)
        self.client.put_object(
            Bucket=self.config.bucket,
            Key=object_key,
            Body=data,
            ContentType=content_type,
        )
        return f"s3://{self.config.bucket}/{object_key}"

    def save_json(self, key: str, payload):
        data = json.dumps(payload, indent=2, default=str).encode("utf-8")
        return self.save_bytes(key, data, "application/json")

    def test_connection(self):
        if self.backend == "local":
            probe = self.save_bytes("_connection_test.txt", b"FORGE storage OK", "text/plain")
            return True, probe

        self.client.head_bucket(Bucket=self.config.bucket)
        probe = self.save_bytes("_connection_test.txt", b"FORGE storage OK", "text/plain")
        return True, probe
