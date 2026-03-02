import { apiGet, apiPost } from "./api";

interface PresignResponse {
  upload_url: string;
  s3_key: string;
}

export async function uploadFile(
  file: File,
  entityType: string,
  entityId?: string
): Promise<string> {
  // 1. Get presigned URL
  const { upload_url, s3_key } = await apiPost<PresignResponse>(
    "/v1/files/presign-upload",
    {
      file_name: file.name,
      content_type: file.type || "application/octet-stream",
      entity_type: entityType,
      entity_id: entityId,
    }
  );

  // 2. Upload directly to S3/MinIO
  await fetch(upload_url, {
    method: "PUT",
    body: file,
    headers: { "Content-Type": file.type || "application/octet-stream" },
  });

  // 3. Confirm upload
  await apiPost(
    `/v1/files/confirm-upload?s3_key=${encodeURIComponent(s3_key)}&entity_type=${entityType}&entity_id=${entityId || ""}`
  );

  return s3_key;
}

export async function getDownloadUrl(s3Key: string): Promise<string> {
  const res = await apiGet<{ download_url: string }>(
    `/v1/files/presign-download?s3_key=${encodeURIComponent(s3Key)}`
  );
  return res.download_url;
}
