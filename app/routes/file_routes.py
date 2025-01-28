from flask import Blueprint, request, jsonify, send_file
from app.models import File
from app.models import Visualization
from app.models import VisualizationPermisson
from app.database import db
from azure.storage.blob import BlobClient
import os
from werkzeug.utils import secure_filename
import uuid
from azure.storage.blob import BlobServiceClient
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import pytz

load_dotenv()

file_bp = Blueprint('file', __name__)

# Read all files or a specific file by ID
@file_bp.route('/files', methods=['GET'])
def get_files():
    file_id = request.args.get('file_id')
    if file_id:
        file = File.query.filter_by(file_id=file_id).first()
        if not file:
            return jsonify({"message": "File not found"}), 404
        return jsonify({
            "file_id": file.file_id,
            "pair_id": file.pair_id,
            "hive_giai": file.hive_giai,
            "file_type": file.file_type,
            "file_name": file.file_name,
            "file_url": file.file_url,
            "user_id": file.user_id,
            "farm_id": file.farm_id,
            "created_at": file.created_at.isoformat(),
        })
    else:
        files = File.query.all()
        return jsonify([
            {
                "file_id": file.file_id,
                "pair_id": file.pair_id,
                "hive_giai": file.hive_giai,
                "file_type": file.file_type,
                "file_name": file.file_name,
                "file_url": file.file_url,
                "user_id": file.user_id,
                "farm_id": file.farm_id,
                "created_at": file.created_at.isoformat(),
            } for file in files
        ])

# Update a file by ID
@file_bp.route('/files/<file_id>', methods=['PUT'])
def update_file(file_id):
    data = request.json
    file = File.query.filter_by(file_id=file_id).first()
    if not file:
        return jsonify({"message": "File not found"}), 404

    # Update fields if provided in the request
    if "pair_id" in data:
        file.pair_id = data["pair_id"]
    if "hive_giai" in data:
        file.hive_giai = data["hive_giai"]
    if "file_type" in data:
        file.file_type = data["file_type"]
    if "file_name" in data:
        file.file_name = data["file_name"]
    if "file_url" in data:
        file.file_url = data["file_url"]
    if "user_id" in data:
        file.user_id = data["user_id"]
    if "farm_id" in data:
        file.farm_id = data["farm_id"]

    db.session.commit()
    return jsonify({"message": "File updated successfully"})

# Delete a file by ID
@file_bp.route('/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    file = File.query.filter_by(file_id=file_id).first()
    if not file:
        return jsonify({"message": "File not found"}), 404

    db.session.delete(file)
    
    # Also delete visualization record
    visualization = Visualization.query.filter_by(pair_id=file.pair_id).first()
    if visualization:
        db.session.delete(visualization)
        
    db.session.commit()
    return jsonify({"message": "File deleted successfully"})

account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")

def download_file_from_url_with_auth(blob_url, download_file_path):
    try:
        blob_client = BlobClient.from_blob_url(blob_url, credential=account_key)
        with open(download_file_path, "wb") as file:
            file.write(blob_client.download_blob().readall())
        return download_file_path
    except Exception as e:
        print(f"Error during download: {e}")
        return None

# Download a file from Azure Blob Storage
@file_bp.route("/download", methods=["POST"])
def download_file():
    data = request.json
    blob_url = data.get("blob_url")
    
    if not blob_url:
        return jsonify({"error": "Blob URL is required"}), 400

    # Define the temporary file path
    temp_file_path = os.path.join("/tmp", os.path.basename(blob_url)).replace("\\", "/")
    
    # Ensure the temp directory exists
    os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

    # Print the download path for debugging
    print(f"Downloading file to: {temp_file_path}")
    
    # Download the file
    downloaded_file = download_file_from_url_with_auth(blob_url, temp_file_path)

    if downloaded_file:
        # Ensure the file exists before sending
        if os.path.exists(downloaded_file):
            # Send the file as an attachment, which triggers the download in the browser
            return send_file(downloaded_file, as_attachment=True, download_name=os.path.basename(downloaded_file))
        else:
            return jsonify({"error": "Downloaded file not found"}), 500
    else:
        return jsonify({"error": "Failed to download file"}), 500

connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

# Upload files to Azure Blob Storage and save file records to the database
@file_bp.route("/upload", methods=["POST"])
def upload_files():
    try:
        # Get form data
        farm_id = request.form.get("farmId")
        hive_giai = request.form.get("hiveGiai", "")
        metadata_file = request.files.get("metadataFile")
        barcoding_file = request.files.get("barcodingFile")
        user_id = request.form.get("userId")

        # Validate input
        if not farm_id or not metadata_file or not barcoding_file:
            return jsonify({"error": "Farm ID, Metadata File, and Barcoding File are required."}), 400

        # Generate pair_id for the two files
        pair_id = str(uuid.uuid4())

        # Handle file uploads
        uploaded_files = []
        for file, file_type in [(metadata_file, "metadata"), (barcoding_file, "barcoding")]:
            file_id = str(uuid.uuid4())
            
            # distinguish metadata and barcoding files id
            if file_type == "metadata":
                metadata_file_id = file_id
            else:
                barcoding_file_id = file_id
            filename = secure_filename(file.filename)
            file_extension = os.path.splitext(filename)[1]  # Extract the file extension

            if not file_extension:  # Validate file extension
                return jsonify({"error": f"File {filename} has no extension."}), 400

            file_path = f"{pair_id}/{file_id}{file_extension}"
            blob_client = container_client.get_blob_client(file_path)

            # Clean data if file is barcoding
            if file_type == "barcoding":
                if file_extension in [".xls", ".xlsx"]:
                    df = pd.read_excel(file, sheet_name=None)  # Load all sheets
                    # Remove rows with taxonomy prefixes
                    taxonomy_prefix_pattern = r"^[A-Z]__"
                    for sheet_name, sheet_data in df.items():
                        # Filter rows where all sample columns are zero
                        sample_columns = sheet_data.columns[8:]  # Sample columns start from the 9th column
                        sheet_data = sheet_data.loc[
                            ~sheet_data[sample_columns].eq(0).all(axis=1)
                        ]
                        # Remove rows with taxonomy prefixes
                        df[sheet_name] = sheet_data[
                            ~sheet_data["Genus"].str.contains(taxonomy_prefix_pattern, na=False) &
                            ~sheet_data["Species"].str.contains(taxonomy_prefix_pattern, na=False)
                        ]
                    # Save the cleaned data back to the file before uploading
                    cleaned_file_path = f"/tmp/{file_id}_cleaned.xlsx"
                    with pd.ExcelWriter(cleaned_file_path) as writer:
                        for sheet_name, sheet_data in df.items():
                            sheet_data.to_excel(writer, sheet_name=sheet_name, index=False)
                    file = open(cleaned_file_path, "rb")  # Use cleaned file for upload

            # Upload file to Azure Blob Storage
            blob_client.upload_blob(file, overwrite=True)
            file_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{file_path}"
            
            melbourne_tz = pytz.timezone('Australia/Melbourne')
            melbourne_time = datetime.now(melbourne_tz)

            # Save file record to the database
            new_file = File(
                file_id=file_id,
                pair_id=pair_id,
                hive_giai=hive_giai,
                file_type=file_type,
                file_name=filename,
                file_url=file_url,
                user_id=user_id,
                farm_id=farm_id,
                created_at=melbourne_time
            )
            db.session.add(new_file)
            uploaded_files.append({
                "file_id": file_id,
                "file_type": file_type,
                "file_name": filename,
                "file_url": file_url,
            })
        
        # also add to table t_visualization
        visualization_id = str(uuid.uuid4())
        new_visualization = Visualization(visualization_id=visualization_id, pair_id=pair_id, farm_id=farm_id, metadata_file_id=metadata_file_id, barcoding_file_id=barcoding_file_id)
        db.session.add(new_visualization)
        
        # also add to table t_visualization_permission
        new_visualization_permission = VisualizationPermisson(visualization_id=visualization_id, user_id=user_id)
        db.session.add(new_visualization_permission)
   
        db.session.commit()

        return jsonify({
            "message": "Files uploaded successfully.",
            "uploaded_files": uploaded_files,
        }), 200

    except Exception as e:
        print("Error:", str(e))
        
        return jsonify({"error": "An error occurred during file upload."}), 500

