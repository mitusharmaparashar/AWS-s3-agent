import json
import boto3

def lambda_handler(event, context):
    print("=== EVENT START ===")
    print(json.dumps(event))
    print("=== EVENT END ===")

    try:
        action_group = "storage_bucket"
        function_name = event.get("function", "create_bucket_1")  # Identify which function called
        params = {p["name"]: p["value"] for p in event.get("parameters", [])}
        bucket_name = params.get("bucket_name")
        region = params.get("region", "eu-west-2")

        if not bucket_name:
            raise ValueError("Missing parameter: bucket_name")

        s3 = boto3.client("s3", region_name=region)

        # --- CREATE BUCKET FUNCTION ---
        if function_name == "create_bucket_1":
            print(f"➡️ Checking if bucket '{bucket_name}' already exists...")
            existing_buckets = s3.list_buckets()
            for b in existing_buckets.get("Buckets", []):
                if b["Name"] == bucket_name:
                    message = f"⚠️ Bucket '{bucket_name}' already exists in your account."
                    print(message)
                    return bedrock_response(action_group, function_name, message)

            print(f"➡️ Creating bucket '{bucket_name}' in '{region}'...")
            if region == "us-east-1":
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": region}
                )
            message = f"✅ S3 bucket '{bucket_name}' created successfully in region '{region}'."
            print(message)
            return bedrock_response(action_group, function_name, message)

        # --- DELETE BUCKET FUNCTION ---
        elif function_name == "delete_bucket_1":
            print(f"➡️ Attempting to delete bucket '{bucket_name}' in '{region}'...")
            try:
                s3.delete_bucket(Bucket=bucket_name)
                message = f"🗑️ S3 bucket '{bucket_name}' deleted successfully from region '{region}'."
            except s3.exceptions.ClientError as e:
                if "NoSuchBucket" in str(e):
                    message = f"⚠️ Bucket '{bucket_name}' does not exist."
                else:
                    raise
            print(message)
            return bedrock_response(action_group, function_name, message)

        else:
            raise ValueError(f"Unknown function name: {function_name}")

    except Exception as e:
        message = f"❌ Error: {str(e)}"
        print(message)
        return bedrock_response(action_group, "error_handler", message)


def bedrock_response(action_group, function_name, message):
    """Return Bedrock-compliant response"""
    return {
        "response": {
            "actionGroup": action_group,
            "function": function_name,
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": message
                    }
                }
            }
        }
    }
