import logging
import alibabacloud_oss_v2 as oss
import alibabacloud_oss_v2.aio as oss_aio
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_async_client: oss_aio.AsyncClient | None = None


def get_oss_config() -> oss.Config:
    credentials_provider = oss.credentials.StaticCredentialsProvider(
        access_key_id=settings.OSS_ACCESS_KEY_ID,
        access_key_secret=settings.OSS_ACCESS_KEY_SECRET,
    )
    cfg = oss.Config(
        region=settings.OSS_REGION,
        endpoint=settings.OSS_ENDPOINT,
        credentials_provider=credentials_provider,
    )
    return cfg


def get_async_oss_client() -> oss_aio.AsyncClient:
    global _async_client
    if _async_client is None:
        logger.info(f"Initializing OSS async client: endpoint={settings.OSS_ENDPOINT}, region={settings.OSS_REGION}, bucket={settings.OSS_BUCKET}")
        cfg = get_oss_config()
        _async_client = oss_aio.AsyncClient(cfg)
        logger.info("OSS async client initialized successfully")
    return _async_client


async def close_oss_client():
    global _async_client
    if _async_client is not None:
        await _async_client.close()
        _async_client = None
        logger.info("OSS async client closed")


def get_oss_url(key: str) -> str:
    if settings.OSS_CUSTOM_DOMAIN:
        domain = settings.OSS_CUSTOM_DOMAIN.rstrip("/")
        return f"{domain}/{key}"
    return f"/api/oss/image/{key}"


async def upload_bytes(key: str, data: bytes, content_type: str = "image/jpeg") -> str:
    client = get_async_oss_client()
    request = oss.PutObjectRequest(
        bucket=settings.OSS_BUCKET,
        key=key,
        body=data,
        content_type=content_type,
    )
    result = await client.put_object(request)
    if result.status_code == 200:
        url = get_oss_url(key)
        logger.info(f"OSS upload success: {key} -> {url}")
        return url
    else:
        raise Exception(f"OSS upload failed: status={result.status_code}, request_id={result.request_id}")


async def get_object_bytes(key: str) -> tuple[bytes, str]:
    client = get_async_oss_client()
    request = oss.GetObjectRequest(
        bucket=settings.OSS_BUCKET,
        key=key,
    )
    logger.info(f"OSS get_object: bucket={settings.OSS_BUCKET}, key={key}")
    result = await client.get_object(request)
    if result.status_code == 200:
        content_type = result.content_type or "application/octet-stream"
        body = await result.body.read()
        logger.info(f"OSS get_object success: key={key}, content_type={content_type}, size={len(body)}")
        return body, content_type
    else:
        logger.error(f"OSS get_object failed: status={result.status_code}, key={key}")
        raise Exception(f"OSS get object failed: status={result.status_code}, key={key}")


async def delete_object(key: str) -> bool:
    client = get_async_oss_client()
    request = oss.DeleteObjectRequest(
        bucket=settings.OSS_BUCKET,
        key=key,
    )
    result = await client.delete_object(request)
    if result.status_code == 204:
        logger.info(f"OSS delete success: {key}")
        return True
    else:
        logger.error(f"OSS delete failed: {key}, status={result.status_code}")
        return False


def extract_key_from_url(url: str) -> str:
    if settings.OSS_CUSTOM_DOMAIN:
        domain = settings.OSS_CUSTOM_DOMAIN.rstrip("/")
        prefix = f"{domain}/"
        if url.startswith(prefix):
            return url[len(prefix):]
    proxy_prefix = "/api/oss/image/"
    if url.startswith(proxy_prefix):
        return url[len(proxy_prefix):]
    default_prefix = f"https://{settings.OSS_BUCKET}.{settings.OSS_ENDPOINT.replace('https://', '').replace('http://', '')}/"
    if url.startswith(default_prefix):
        return url[len(default_prefix):]
    return url
