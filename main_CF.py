import functions_framework
from flask import request, jsonify
from deepface import DeepFace
from google.cloud import storage
import os
# import shutil
import tempfile


# def require_api_key(func):
#     def wrapper(*args, **kwargs):
#         api_key = request.headers.get('Authorization')
#         if api_key and api_key == "1234567890qwertyuiop":
#             return func(*args, **kwargs)
#         else:
#             return jsonify({
#                 "error": "true",
#                 "message": "Unauthorized"
#                 }), 401
#     return wrapper

# @require_api_key
@functions_framework.http
def compare_faces_and_copy(request):
    
    api_key = request.headers.get('Authorization')
    if not api_key or api_key != "1234567890qwertyuiop":
        return jsonify({
            "error": "true",
            "message": "Unauthorized"
        }), 401

    try:
        folder_id = request.json.get("id")
        image_id = request.json.get("image_id")

        # Configure your bucket and file paths
        bucket_name = "appsheet_rnd"
        input_image = f"face_match/face_match_data_image/{image_id}"
        image_folder = "face_match/face_match_dummy_face/"
        new_folder = f"face_match/face_match_result/{folder_id}/"  # Destination folder in GCS with a random name
        
        with tempfile.TemporaryDirectory() as tmp_folder:
            # Setup local paths
            local_folder_face = os.path.join(tmp_folder, 'face')
            local_folder_images = os.path.join(tmp_folder, 'images')
            os.makedirs(local_folder_face, exist_ok=True)
            os.makedirs(local_folder_images, exist_ok=True)

            # Download images
            image_path = os.path.join(local_folder_face, image_id)
            download_from_gcs(bucket_name, input_image, image_path)
            download_folder_from_gcs(bucket_name, image_folder, local_folder_images)

            # Run DeepFace find
            find = DeepFace.find(
                img_path=image_path,
                db_path=local_folder_images,
                model_name="VGG-Face",
                distance_metric="euclidean",
                enforce_detection=True,
                detector_backend="opencv",
                align=True,
                expand_percentage=0,
                threshold=None,
                normalization="base",
                silent=False,
                refresh_database=True,
                anti_spoofing=False,
            )

            # Filter results
            filtered_df = find[0][find[0]['distance'] < 1]
            if filtered_df.empty:
                return jsonify({
                    "error": "false",
                    "message": "No matches found",
                }), 200

            result_ids = [os.path.basename(identity) for identity in filtered_df['identity']]
            copy_images_to_new_folder(bucket_name, image_folder, new_folder, result_ids)

        return jsonify({
            "error": "false",
            "message": f"Matching images copied to {new_folder}",
            "ids": result_ids
        }), 200
        # delete_local_tmp_folder(tmp_folder)

        # return jsonify({
        #     "error": "false",
        #     "message": f"Matching images copied to {new_folder}",
        #     "ids": result_ids
        # }), 200

        # # Delete local tmp folder

        # # Delete tmp folder in GCS
        # delete_gcs_tmp_folder(bucket_name, new_folder)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def download_from_gcs(bucket_name, source_blob_name, destination_file_name):
    """Download a single file from Google Cloud Storage."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

def download_folder_from_gcs(bucket_name, folder_name, local_folder_images):
    """Download all files from a folder in GCS to a local folder."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=folder_name)
    for blob in blobs:
        if not blob.name.endswith("/"):  # Skip directories
            local_file_path = os.path.join(local_folder_images, os.path.basename(blob.name))
            blob.download_to_filename(local_file_path)

def copy_images_to_new_folder(bucket_name, source_folder, new_folder, result_ids):
    """Copy matching images to a new folder in GCS."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    for result_id in result_ids:
        # Construct the source and destination blob paths
        source_blob_name = f"{source_folder}{result_id}"  # Adjust extension if needed
        destination_blob_name = f"{new_folder}{result_id}"
        
        source_blob = bucket.blob(source_blob_name)
        destination_blob = bucket.blob(destination_blob_name)

        if source_blob.exists():
            # Copy the file
            destination_blob.rewrite(source_blob)
            # print(f"Copied {source_blob_name} to {destination_blob_name}")
        else:
            print(f"Source file {source_blob_name} does not exist.")

# def delete_local_tmp_folder(folder):
#     """Delete the local tmp folder."""
#     shutil.rmtree(os.path.join(os.getcwd(), folder), ignore_errors=True)

# if __name__ == "__main__":
#     app.run(port=5000)