import boto3
from core.config import settings
from botocore.exceptions import NoCredentialsError

S3_BUCKET_NAME = settings.S3_BUCKET_NAME

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.REGION_NAME,
)
print("AWS_ACCESS_KEY_ID =", settings.AWS_ACCESS_KEY_ID)
print("AWS_SECRET_ACCESS_KEY =", settings.AWS_SECRET_ACCESS_KEY)
print("REGION_NAME =", settings.REGION_NAME)
print("S3_BUCKET_NAME =", S3_BUCKET_NAME)

def upload_file_to_s3(file_obj, filename: str, content_type: str = None) -> str:
    """
    อัปโหลดไฟล์ไป S3
    content_type: กำหนด Content-Type เช่น 'image/png', 'image/jpeg'
    """
    try:
        extra_args = {"ContentType": content_type} if content_type else {}
        s3_client.upload_fileobj(file_obj, S3_BUCKET_NAME, filename, ExtraArgs=extra_args)
        return f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{filename}"
    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found.")
    except Exception as e:
        raise RuntimeError(f"Failed to upload file: {e}")
    
def get_presigned_url(filename: str, expires_in: int = 3600) -> str:
    """
    คืน URL สำหรับ GET ไฟล์จาก S3 (private bucket)
    expires_in: วินาทีที่ URL ใช้งานได้
    """
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": filename},
            ExpiresIn=expires_in,
        )
        return url
    except Exception as e:
        raise RuntimeError(f"Failed to generate presigned URL: {e}")