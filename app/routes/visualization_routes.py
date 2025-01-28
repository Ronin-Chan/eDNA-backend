from flask import Blueprint, request, jsonify
from app.models import Visualization
from app.models import VisualizationPermisson
from azure.storage.blob import BlobClient
import os
from app.database import db
import pandas as pd
import plotly.express as px
import plotly.io as pio  # For serializing plotly figures
import base64
from mimetypes import guess_type
from openai import AzureOpenAI

account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
container_url = "https://edna0912.blob.core.windows.net/container0912"

visualization_bp = Blueprint('visualization', __name__)

@visualization_bp.route('/visualizations', methods=['GET'])
def getVisualizations():
    visualizations = Visualization.query.all()
    return jsonify([{"id": visualization.visualization_id, "metadata_file_id": visualization.metadata_file_id, "barcoding_file_id": visualization.barcoding_file_id, "pair_id": visualization.pair_id, "created_at": visualization.created_at} for visualization in visualizations]), 200

# get visualization by farm_id
@visualization_bp.route('/visualizations/farm/<farm_id>', methods=['GET'])
def getVisualizationsByFarmId(farm_id):
    visualizations = Visualization.query.filter_by(farm_id=farm_id).all()
    
    return jsonify([{"id": visualization.visualization_id, "metadata_file_id": visualization.metadata_file_id, "barcoding_file_id": visualization.barcoding_file_id, "pair_id": visualization.pair_id, "created_at": visualization.created_at} for visualization in visualizations]), 200

# get visualization by user_id
@visualization_bp.route('/visualizations/user/<user_id>', methods=['GET'])
def getVisualizationsByUserId(user_id):
    visualizationPermissons = VisualizationPermisson.query.filter_by(user_id=user_id).all()
    
    visualizations = Visualization.query.filter(Visualization.visualization_id.in_([visualizationPermisson.visualization_id for visualizationPermisson in visualizationPermissons])).all()
    
    return jsonify([{"id": visualization.visualization_id, "metadata_file_id": visualization.metadata_file_id, "barcoding_file_id": visualization.barcoding_file_id, "pair_id": visualization.pair_id, "created_at": visualization.created_at} for visualization in visualizations]), 200


@visualization_bp.route('/visualizations/<visualization_id>', methods=['GET'])
def getVisualization(visualization_id):
    print(f"Fetching visualization with ID: {visualization_id}")
    # Query the visualization from the database
    visualization = Visualization.query.filter_by(visualization_id=visualization_id).first()
    if not visualization:
        return jsonify({"message": "Visualization not found"}), 404

    pair_id = visualization.pair_id
    metadata_file_id = visualization.metadata_file_id
    barcoding_file_id = visualization.barcoding_file_id

    # Construct Azure Blob URLs
    metadata_blob_url = f"{container_url}/{pair_id}/{metadata_file_id}.csv"
    barcoding_blob_url = f"{container_url}/{pair_id}/{barcoding_file_id}.xlsx"

    # Define temporary paths for downloaded files
    metadata_temp_path = os.path.join("/tmp", f"{metadata_file_id}.csv").replace("\\", "/")
    barcoding_temp_path = os.path.join("/tmp", f"{barcoding_file_id}.xlsx").replace("\\", "/")

    # Download the files
    download_file_from_url_with_auth(metadata_blob_url, metadata_temp_path)
    download_file_from_url_with_auth(barcoding_blob_url, barcoding_temp_path)

    # Load metadata and barcoding data
    metadata_df = pd.read_csv(metadata_temp_path)
    all_sheets = pd.read_excel(barcoding_temp_path, sheet_name=None)
    
    # Generate diagrams for all combinations of farm, hive, and date
    farms = metadata_df["Location"].dropna().unique()
    hives = metadata_df["Hive"].dropna().unique()
    dates = metadata_df["Date"].dropna().unique()

    # Generate sunburst diagrams for all sheets
    all_diagrams = {}
    for farm in farms:
        for hive in hives:
            for date in dates:
                diagrams = {}
                for sheet_name, sheet_data in all_sheets.items():
                    fig = process_sheet(sheet_name, sheet_data, metadata_df, farm, hive, date)
                    if fig:
                        diagrams[sheet_name] = pio.to_json(fig)
                all_diagrams[f"{farm}-{hive}-{date}"] = diagrams

    return jsonify({"diagrams": all_diagrams}), 200
       
def download_file_from_url_with_auth(blob_url, download_file_path):
    try:
        blob_client = BlobClient.from_blob_url(blob_url, credential=account_key)
        
        # blob_data = blob_client.download_blob().readall()
        
        with open(download_file_path, "wb") as file:
            file.write(blob_client.download_blob().readall())
            
        return download_file_path
    except Exception as e:
        print(f"Error during download: {e}")
        return None
    
# Function to process a single sheet and generate a sunburst diagram
def process_sheet(sheet_name, barcoding_df, metadata_df, selected_location, selected_hive, selected_date):
    taxonomy_columns = ["Class", "Genus"] if sheet_name in ["Fungi", "Bacteria"] else ["Class", "Genus", "Species"]
    sample_columns = barcoding_df.columns[8:]

    # Filter metadata
    filtered_metadata = metadata_df[
        (metadata_df["Location"] == selected_location) &
        (metadata_df["Hive"] == selected_hive) &
        (metadata_df["Date"] == selected_date)
    ]
    
    # print(f"Filtered Metadata:\n{filtered_metadata.head()}")

    melted_bacteria = barcoding_df.melt(
        id_vars=taxonomy_columns,
        value_vars=sample_columns,
        var_name="Sample",
        value_name="Presence",
    )

    merged_data = melted_bacteria.merge(
        filtered_metadata, left_on="Sample", right_on="ESV_ID", how="inner"
    )

    filtered_data = merged_data[merged_data["Presence"] > 0]
    
    sunburst_data = (
        filtered_data.groupby(taxonomy_columns)
        .agg(
            Count=("Presence", lambda x: (x > 0).sum()),
            Hive=("Hive", lambda x: ", ".join(x.dropna().astype(str).unique())),
            Location=("Location", lambda x: ", ".join(x.dropna().astype(str).unique())),
            Date=("Date", lambda x: ", ".join(x.dropna().astype(str).unique())),
        )
        .reset_index()
    )

    fig = px.sunburst(
        sunburst_data,
        path=taxonomy_columns,
        values="Count",
        hover_data={"Hive": True, "Location": True, "Date": True, "Count": False},
        title=f"Taxonomy Sunburst for {sheet_name}",
    )
    fig.update_layout(autosize=True, margin=dict(t=50, l=0, r=0, b=0), height=None)

    return fig

azure_open_ai_key = os.getenv("AZURE_OPENAI_API_KEY")

@visualization_bp.route('/ai', methods=['POST'])
def ai_analysis():
    try:
        # Check if the request has both an image and a question
        if 'image' not in request.files or 'question' not in request.form:
            return jsonify({"error": "Image and question are required."}), 400

        # Get the image and question from the request
        image_file = request.files['image']
        question = request.form['question']
        chatHistory = request.form['chatHistory']

        # Read and encode the image file into a data URL
        mime_type = image_file.mimetype or 'application/octet-stream'
        base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_encoded_data}"

        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            api_key=azure_open_ai_key,
            api_version="2024-05-01-preview",
            azure_endpoint="https://openai1012.openai.azure.com/"
        )

        # Specify the model deployment name
        deployment_name = "gpt-4o"  # Replace with your deployment name

        # Send a request to Azure OpenAI
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant helping people answer questions related to the image. Please provide an answer to the question in plain text."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Chat history FYI:" + chatHistory},
                        {"type": "text", "text": "Answer this question:" + question},
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ]
                }
            ],
            max_tokens=2000
        )

        # Extract and return the AI's response
        ai_response = response.choices[0].message.content
        return jsonify({"response": ai_response}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@visualization_bp.route('/assign-permission', methods=['POST'])
def assign_permission():
    data = request.get_json()
    farmer_id = data.get("farmer_id")
    visualization_id = data.get("visualization_id")
    
    visualization_permission = VisualizationPermisson(
        user_id=farmer_id,
        visualization_id=visualization_id,
    )
    
    db.session.add(visualization_permission)
    db.session.commit()
    
    return jsonify({"message": "Permission assigned successfully"}), 201
