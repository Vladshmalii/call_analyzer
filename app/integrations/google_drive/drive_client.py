import asyncio
import os
from typing import Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import structlog
from app.core.config.settings import settings

logger = structlog.get_logger(__name__)

class GoogleDriveClient:
    def __init__(self):
        self.credentials_path = settings.GOOGLE_CREDENTIALS_PATH
        self.source_folder_id = settings.GOOGLE_DRIVE_SOURCE_FOLDER_ID
        self.working_folder_id = settings.GOOGLE_DRIVE_WORKING_FOLDER_ID
        self.service = None

    def _get_service(self):
        if not self.service:
            if not os.path.exists(self.credentials_path):
                logger.warning("Google credentials file not found, running in mock/offline mode")
                return None
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/drive"]
            )
            self.service = build("drive", "v3", credentials=credentials)
        return self.service

    async def list_files(self) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._list_files_sync)

    def _list_files_sync(self) -> list[dict[str, Any]]:
        service = self._get_service()
        if not service:
            return []

        query = f"'{self.source_folder_id}' in parents and trashed = false"
        try:
            results = service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime)"
            ).execute()
            files = results.get("files", [])
            supported_extensions = (".mp3", ".wav", ".m4a", ".ogg")
            filtered_files = [
                f for f in files
                if f.get("name", "").lower().endswith(supported_extensions)
            ]
            return filtered_files
        except Exception as e:
            logger.error("Error scanning Google Drive", error=str(e))
            return []

    async def create_shortcut(self, file_id: str, file_name: str) -> bool:
        return await asyncio.to_thread(self._create_shortcut_sync, file_id, file_name)

    def _create_shortcut_sync(self, file_id: str, file_name: str) -> bool:
        service = self._get_service()
        if not service:
            return False
        try:
            shortcut_metadata = {
                "name": file_name,
                "mimeType": "application/vnd.google-apps.shortcut",
                "shortcutDetails": {
                    "targetId": file_id
                },
                "parents": [self.working_folder_id]
            }
            service.files().create(
                body=shortcut_metadata,
                fields="id"
            ).execute()
            logger.info("Shortcut created in working folder", file_id=file_id, file_name=file_name)
            return True
        except Exception as e:
            logger.error("Error creating shortcut in working folder", file_id=file_id, error=str(e))
            return False

    async def download_file(self, file_id: str, destination_path: str) -> bool:
        return await asyncio.to_thread(self._download_file_sync, file_id, destination_path)

    def _download_file_sync(self, file_id: str, destination_path: str) -> bool:
        service = self._get_service()
        if not service:
            logger.error("Failed to download file: service client not initialized")
            return False

        try:
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            request = service.files().get_media(fileId=file_id)
            with open(destination_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request, chunksize=1024 * 1024)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            logger.info("File downloaded successfully", file_id=file_id, path=destination_path)
            return True
        except Exception as e:
            logger.error("Error downloading file from Google Drive", file_id=file_id, error=str(e))
            if os.path.exists(destination_path):
                os.remove(destination_path)
            return False
