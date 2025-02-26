from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from werkzeug.utils import secure_filename
import os
import PyPDF2
import joblib

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

import joblib
import os

# Get the correct model path
backend_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(backend_dir, "best_model_xgb.pkl")

try:
    model = joblib.load(model_path)  # Load using joblib
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {str(e)}")
    model = None




def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_features_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

    # Split text into lines
    lines = text.split('\n')

    # Extract header and data
    header_line = None
    data_line = None

    for line in lines:
        # Make case-insensitive comparison
        if "hematocrit" in line.lower() and "sex" in line.lower():
            header_line = line
        elif header_line and any(char.isdigit() for char in line):
            data_line = line
            break

    if header_line and data_line:
        # Clean and split into values
        headers = header_line.split()
        values = data_line.split()

        if len(headers) == len(values):
            # Create case-insensitive mapping
            extracted_data = {}
            for header, value in zip(headers, values):
                extracted_data[header.upper()] = value
            
            # Define feature mappings (common variations of names)
            feature_mappings = {
                'Hematocrit': ['HEMATOCRIT', 'HCT'],
                'Hemoglobin': ['HEMOGLOBIN', 'HGB', 'HB'],
                'Erythrocyte': ['ERYTHROCYTE', 'RBC'],
                'Leucocyte': ['LEUCOCYTE', 'WBC'],
                'Thrombocyte': ['THROMBOCYTE', 'PLT'],
                'Mch': ['MCH'],
                'Mchc': ['MCHC'],
                'Mcv': ['MCV'],
                'Age': ['AGE'],
                'Sex': ['SEX']
            }
            
            # Extract features using mappings
            features = []
            normalized_data = {}
            
            for feature, aliases in feature_mappings.items():
                value = None
                for alias in aliases:
                    if alias in extracted_data:
                        value = extracted_data[alias]
                        normalized_data[feature] = value
                        break
                
                if value is None:
                    print(f"Missing feature: {feature}")
                    print("Available features:", extracted_data.keys())
                    raise ValueError(f"Missing required feature: {feature}")
                
                try:
                    features.append(float(value))
                except ValueError:
                    raise ValueError(f"Invalid value for {feature}: {value}")
            
            return features, normalized_data
        else:
            raise ValueError("Mismatch between header and data columns.")
    else:
        raise ValueError("Could not locate headers or data in the PDF.")

def analyze_blood_report(features):
    results = {
        'conditions': [],
        'findings': [],
        'treatments': []
    }
    
    # Anemia Analysis
    if features['Hemoglobin'] < 12 and features['Hematocrit'] < 36:
        if features['Mcv'] < 80:
            results['conditions'].append("Microcytic Anemia")
            results['findings'].append(
                "Low hemoglobin, hematocrit, and MCV indicate iron deficiency anemia"
            )
            results['treatments'].extend([
                "Prescribe iron supplements (ferrous sulfate 325mg oral daily)",
                "Dietary modifications: increase iron-rich foods",
                "Follow-up blood test in 3 months"
            ])
        elif features['Mcv'] > 100:
            results['conditions'].append("Macrocytic Anemia")
            results['findings'].append(
                "Low hemoglobin with high MCV suggests vitamin B12 or folate deficiency"
            )
            results['treatments'].extend([
                "Vitamin B12 injections or oral supplements",
                "Folic acid supplementation",
                "Dietary counseling for B12 and folate-rich foods"
            ])
    
    # Add other conditions as in your code...
    # Infection/Inflammation Analysis
    if features['Leucocyte'] > 11:
        results['conditions'].append("Leukocytosis")
        results['findings'].append(
            "Elevated white blood cell count indicates possible infection or inflammation"
        )
        results['treatments'].extend([
            "Further testing to identify infection source",
            "Consider CBC with differential",
            "Possible antibiotic therapy based on infection source"
        ])
    
    return results

def generate_report(analysis_results, feature_dict):
    report = "BLOOD ANALYSIS REPORT\n\n"
    
    if analysis_results['conditions']:
        report += "Identified Conditions:\n"
        for condition in analysis_results['conditions']:
            report += f"• <span class='text-danger'>{condition}</span>\n"
        
        report += "\nClinical Findings:\n"
        for finding in analysis_results['findings']:
            # Add values for hemoglobin, hematocrit, and MCV findings
            if "hemoglobin" in finding.lower():
                report += f"• <span class='text-danger'>{finding}</span>\n  Values:\n"
                report += f"  - Hemoglobin: <span class='text-danger'>{feature_dict['Hemoglobin']:.1f} g/dL</span> (Normal: 12-16 g/dL)\n"
                report += f"  - Hematocrit: <span class='text-danger'>{feature_dict['Hematocrit']:.1f}%</span> (Normal: 36-48%)\n"
                report += f"  - MCV: <span class='text-danger'>{feature_dict['Mcv']:.1f} fL</span> (Normal: 80-100 fL)\n"
            # Add values for leucocyte findings
            elif "white blood cell" in finding.lower():
                report += f"• <span class='text-danger'>{finding}</span>\n  Values:\n"
                report += f"  - Leucocyte: <span class='text-danger'>{feature_dict['Leucocyte']:.1f} x10^9/L</span> (Normal: 4-11 x10^9/L)\n"
            # Add values for thrombocyte findings
            elif "platelet" in finding.lower():
                report += f"• <span class='text-danger'>{finding}</span>\n  Values:\n"
                report += f"  - Thrombocyte: <span class='text-danger'>{feature_dict['Thrombocyte']:.1f} x10^9/L</span> (Normal: 150-450 x10^9/L)\n"
            else:
                report += f"• <span class='text-danger'>{finding}</span>\n"
        
        report += "\nTreatment Recommendations:\n"
        for treatment in analysis_results['treatments']:
            report += f"• {treatment}\n"
    else:
        return generate_normal_report(feature_dict)
    
    return report

def generate_normal_report(feature_dict):
    report = "BLOOD ANALYSIS REPORT\n\n"
    report += "Identified Conditions:\n"
    report += "• <span class='text-success'>No abnormal conditions detected</span>\n\n"
    
    report += "Clinical Findings:\n"
    report += "• <span class='text-success'>All blood parameters are within normal ranges</span>\n\n"
    
    report += "Treatment Recommendations:\n"
    report += "• Maintain current health status\n"
    report += "• Continue regular exercise and balanced diet\n"
    report += "• Schedule routine follow-up in 12 months\n"
    
    return report

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
            
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        if model is None:
            return jsonify({"error": "Model not loaded"}), 500

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            features, extracted_values = extract_features_from_pdf(filepath)
            prediction = model.predict([features])[0]
            
            # Print debug information
            print("Extracted Features:", features)
            print("Prediction:", prediction)
            
            feature_dict = {
                'Hematocrit': float(features[0]),
                'Hemoglobin': float(features[1]),
                'Erythrocyte': float(features[2]),
                'Leucocyte': float(features[3]),
                'Thrombocyte': float(features[4]),
                'Mch': float(features[5]),
                'Mchc': float(features[6]),
                'Mcv': float(features[7]),
                'Age': float(features[8]),
                'Sex': float(features[9])
            }
            
            if prediction == 1:
                analysis = analyze_blood_report(feature_dict)
                detailed_report = generate_report(analysis, feature_dict)
            else:
                detailed_report = generate_normal_report(feature_dict)
            
            return jsonify({
                "status": "success",
                "prediction": "Yes" if prediction == 1 else "No",
                "detailed_analysis": detailed_report
            })

        except Exception as e:
            print("Extraction Error:", str(e))
            response_data = {
                "status": "error",
                "error": f"Feature extraction failed: {str(e)}"
            }
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
            
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/predict_manual', methods=['POST'])
def predict_manual():
    try:
        data = request.json
        features = [
            float(data['Hematocrit']),
            float(data['Hemoglobin']),
            float(data['Erythrocyte']),
            float(data['Leucocyte']),
            float(data['Thrombocyte']),
            float(data['Mch']),
            float(data['Mchc']),
            float(data['Mcv']),
            float(data['Age']),
            float(data['Sex'])
        ]

        prediction = model.predict([features])[0]
        print("Prediction:", prediction)  # Debug print

        if prediction == 1:
            analysis = analyze_blood_report(data)
            detailed_report = generate_report(analysis, data)
        else:
            detailed_report = generate_normal_report(data)
            
        return jsonify({
            "status": "success",
            "prediction": "Yes" if prediction == 1 else "No",
            "detailed_analysis": detailed_report
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000) 
