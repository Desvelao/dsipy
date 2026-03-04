from abc import ABC, abstractmethod
from typing import Optional
import boto3
import base64
import requests

class FeedProvider(ABC):
    """Base class for feed publishing providers."""

    @abstractmethod
    def get_remote(self, path: str) -> tuple[Optional[str], Optional[str]]:
        """Return (content, version/etag) or (None, None) if missing."""
        pass

    @abstractmethod
    def publish(self, path: str, content: str, version: Optional[str]):
        """Publish content to remote provider."""
        pass


class GitHubProvider(FeedProvider):
    def __init__(self, owner: str, repo: str, branch: str, token: str):
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.token = token
        self.headers = {"Authorization": f"token {token}"}

    def _url(self, path: str):
        return f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{path}"

    def get_remote(self, path: str):
        url = self._url(path) + f"?ref={self.branch}"
        resp = requests.get(url, headers=self.headers)
        if resp.status_code == 404:
            return None, None
        resp.raise_for_status()
        data = resp.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content, data["sha"]

    def publish(self, path: str, content: str, version: Optional[str]):
        url = self._url(path)
        payload = {
            "message": f"Update feed: {path}",
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "branch": self.branch,
        }
        if version:
            payload["sha"] = version
        resp = requests.put(url, headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()

class S3Provider(FeedProvider):
    def __init__(self, bucket: str, prefix: str = "", region: str = None):
        self.bucket = bucket
        self.prefix = prefix
        self.s3 = boto3.client("s3", region_name=region)

    def _key(self, path: str):
        return f"{self.prefix}{path}" if self.prefix else path

    def get_remote(self, path: str):
        key = self._key(path)
        try:
            obj = self.s3.get_object(Bucket=self.bucket, Key=key)
            content = obj["Body"].read().decode("utf-8")
            etag = obj["ETag"].strip('"')
            return content, etag
        except self.s3.exceptions.NoSuchKey:
            return None, None

    def publish(self, path: str, content: str, version: Optional[str]):
        key = self._key(path)
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content.encode("utf-8"),
            ContentType="application/xml",
        )


def get_publisher(provider_type: str, **kwargs) -> FeedProvider:
    """Factory function to get the appropriate feed publisher provider.
    
    Args:
        provider_type: Type of provider ('github' or 's3')
        **kwargs: Provider-specific arguments
        
    Returns:
        FeedProvider instance
        
    Raises:
        ValueError: If provider_type is not supported
    """
    provider_type = provider_type.lower()
    if provider_type == "github":
        return GitHubProvider(
            owner=kwargs["owner"],
            repo=kwargs["repo"],
            branch=kwargs["branch"],
            token=kwargs["token"]
        )
    elif provider_type == "s3":
        return S3Provider(
            bucket=kwargs["bucket"],
            prefix=kwargs.get("prefix", ""),
            region=kwargs.get("region")
        )
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")