"""MinIO 对象存储客户端（框架基础设施）。

定位
----
与 ``config/get_redis.py`` 的 ``RedisUtil``、``config/get_scheduler.py`` 的
``SchedulerUtil`` 同列——配置型、有状态、单例的框架基础设施。MinIO 是通用对象
存储，不独属于任何业务模块（反身性用来存 RAG 文档，律师产品可用来存案件/语音文件），
故放在框架层 ``config/`` 下，配置读 ``config.env.MinioConfig``。

启动时由 ``server.py`` lifespan 预热（fail-soft：连不上仅警告，不阻断启动），
业务模块按需 ``MinioUtil.get_instance()`` 取用即可。

参考 ragflow/rag/utils/minio_conn.py 的 RAGFlowMinio 类，简化为单 bucket 模式：
去掉多租户、prefix_path 等复杂逻辑，只保留核心的 put/get/presigned_url。
"""
import time
from io import BytesIO
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from config.env import MinioConfig
from utils.log_util import logger


class MinioUtil:
    """
    MinIO 客户端封装（单 bucket 模式）。

    用法:
        client = MinioUtil.get_instance()
        # 上传
        client.put("documents/xxx.pdf", file_bytes)
        # 下载
        data = client.get("documents/xxx.pdf")
        # 获取预览 URL（7天有效）
        url = client.get_presigned_url("documents/xxx.pdf")
    """

    _instance = None

    def __init__(self):
        self._conn = None
        self._bucket = MinioConfig.minio_bucket
        self._connect()

    @classmethod
    def get_instance(cls) -> 'MinioUtil':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _connect(self):
        """建立 MinIO 连接"""
        try:
            self._conn = Minio(
                MinioConfig.minio_host,
                access_key=MinioConfig.minio_access_key,
                secret_key=MinioConfig.minio_secret_key,
                secure=MinioConfig.minio_secure,
            )
            # 确保 bucket 存在
            if not self._conn.bucket_exists(self._bucket):
                self._conn.make_bucket(self._bucket)
                logger.info(f"MinIO: 创建存储桶 {self._bucket}")
            logger.info(f"MinIO: 连接成功 {MinioConfig.minio_host}, bucket={self._bucket}")
        except Exception as e:
            logger.error(f"MinIO: 连接失败 {MinioConfig.minio_host}: {e}")
            raise

    def _reconnect(self):
        """重连"""
        try:
            if self._conn:
                del self._conn
        except Exception:
            pass
        self._connect()

    def put(self, object_name: str, data: bytes) -> str:
        """
        上传文件到 MinIO
        参考 ragflow minio_conn.py 的 put() 方法

        Args:
            object_name: 对象名称（如 "rag/2024/xxx.pdf"）
            data: 文件二进制数据

        Returns:
            object_name
        """
        for attempt in range(3):
            try:
                self._conn.put_object(
                    self._bucket,
                    object_name,
                    BytesIO(data),
                    len(data),
                )
                logger.info(f"MinIO: 上传成功 {self._bucket}/{object_name} ({len(data)} bytes)")
                return object_name
            except Exception as e:
                logger.error(f"MinIO: 上传失败 (attempt {attempt + 1}/3) {object_name}: {e}")
                self._reconnect()
                time.sleep(1)
        raise RuntimeError(f"MinIO: 上传失败，已重试3次 {object_name}")

    def get(self, object_name: str) -> bytes | None:
        """
        从 MinIO 下载文件
        参考 ragflow minio_conn.py 的 get() 方法

        Args:
            object_name: 对象名称

        Returns:
            文件二进制数据，不存在返回 None
        """
        try:
            response = self._conn.get_object(self._bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            if e.code in ("NoSuchKey", "NoSuchBucket", "ResourceNotFound"):
                logger.warning(f"MinIO: 文件不存在 {object_name}")
                return None
            logger.error(f"MinIO: 下载失败 {object_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"MinIO: 下载失败 {object_name}: {e}")
            self._reconnect()
            return None

    def get_presigned_url(self, object_name: str, expires_hours: int = 168) -> str | None:
        """
        获取文件预签名 URL（用于前端直接预览/下载）
        参考 ragflow minio_conn.py 的 get_presigned_url() 方法

        Args:
            object_name: 对象名称
            expires_hours: URL 有效期（小时），默认7天

        Returns:
            预签名 URL
        """
        try:
            url = self._conn.get_presigned_url(
                "GET",
                self._bucket,
                object_name,
                expires=timedelta(hours=expires_hours),
            )
            return url
        except Exception as e:
            logger.error(f"MinIO: 获取预签名URL失败 {object_name}: {e}")
            return None

    def exists(self, object_name: str) -> bool:
        """
        检查文件是否存在
        参考 ragflow minio_conn.py 的 obj_exist() 方法
        """
        try:
            self._conn.stat_object(self._bucket, object_name)
            return True
        except S3Error as e:
            if e.code in ("NoSuchKey", "NoSuchBucket", "ResourceNotFound"):
                return False
            logger.error(f"MinIO: 检查文件存在失败 {object_name}: {e}")
            return False

    def remove(self, object_name: str):
        """
        删除文件
        参考 ragflow minio_conn.py 的 rm() 方法
        """
        try:
            self._conn.remove_object(self._bucket, object_name)
            logger.info(f"MinIO: 删除成功 {object_name}")
        except Exception as e:
            logger.error(f"MinIO: 删除失败 {object_name}: {e}")

    def list_objects(self, prefix: str = "") -> list[str]:
        """
        列出指定前缀下的所有文件
        """
        try:
            objects = self._conn.list_objects(self._bucket, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except Exception as e:
            logger.error(f"MinIO: 列出文件失败 prefix={prefix}: {e}")
            return []
