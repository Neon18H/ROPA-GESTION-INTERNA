# Deploy notes (Railway + Tigris S3)

## Product media rendering modes

This project supports two modes for product images, controlled by `MEDIA_PUBLIC_READ`:

- `MEDIA_PUBLIC_READ=false` (default): private bucket/object access with signed URLs (`AWS_QUERYSTRING_AUTH=True`).
- `MEDIA_PUBLIC_READ=true`: public read for `media/*` and unsigned URLs.

Required env vars (already used by the app):

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_STORAGE_BUCKET_NAME`
- `AWS_S3_ENDPOINT_URL` (example: `https://t3.storageapi.dev`)
- `AWS_S3_REGION_NAME`
- `MEDIA_PUBLIC_READ` (`true`/`false`, defaults to `false`)

## Bucket policy when `MEDIA_PUBLIC_READ=true`

> Replace `<bucket>` with your real bucket name (for example `enclosed-canister-iwl6gk7`).

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowPublicReadMediaPrefix",
      "Effect": "Allow",
      "Principal": "*",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::<bucket>/media/*"
    }
  ]
}
```

## Quick verification

1. Django URL generation:

```bash
python manage.py shell -c "from apps.inventory.models import Product; p=Product.objects.filter(image__isnull=False).first(); print(p.image.url if p else 'NO_IMAGE')"
```

2. HTTP visibility test (replace URL):

```bash
curl -I "https://t3.storageapi.dev/<bucket>/media/org_<org_id>/products/<product_id>/file.png"
```

Expected:

- public mode: `200 OK` without signing query params.
- private mode: use `product.image.url` output (signed URL) and verify with `curl -I`.


3. Signature check (private mode): ensure output contains `X-Amz-Signature` in query params.
