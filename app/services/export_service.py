import csv
import io
from flask import Response

def generate_csv_export(data, filename="export.csv"):
    """
    Generate a CSV export from a list of dictionaries.
    
    Args:
        data (list): List of dictionaries containing the data.
        filename (str): Name of the file for download.
        
    Returns:
        Response: Flask response object with CSV data.
    """
    if not data:
        return Response("", mimetype="text/csv")
    
    # Get headers from the first item keys
    headers = list(data[0].keys())
    
    # Create an in-memory string buffer
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    
    writer.writeheader()
    writer.writerows(data)
    
    # Create the response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )
