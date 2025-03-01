from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from werkzeug.utils import secure_filename
import os
import pickle
import pandas as pd
from sklearn.preprocessing import LabelEncoder, RobustScaler
import pdfplumber  # Using pdfplumber for PDF extraction
import re  # For regex extraction

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load global objects (model, scaler, and label encoder)
backend_dir = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(backend_dir, "models")
model_path = os.path.join(models_dir, "xgboost_model.sav")
scaler_path = os.path.join(models_dir, "scaler.pkl")
label_encoder_sex_path = os.path.join(models_dir, "label_encoder_sex.pkl")

os.makedirs(models_dir, exist_ok=True)

try:
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    with open(label_encoder_sex_path, 'rb') as f:
        label_encoder_sex = pickle.load(f)
    print("Global objects loaded successfully from models directory!")
except Exception as e:
    print(f"Error loading global objects: {str(e)}")
    model = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_features_from_pdf(pdf_path):
    """
    Extracts required features from a CBC report using pdfplumber.
    This function extracts patient info (Age and Sex) and CBC test values based on
    the provided report format. Expected tests and their labels:
      - Hemoglobin              → "Hemoglobin"
      - Leucocyte               → "Total Leukocyte Count"
      - Thrombocyte             → "Platelet Count" (may include "(Thrombocyte)")
      - Erythrocyte             → "Total RBC Count" (may include "(Erythrocyte)")
      - Hematocrit              → "Hematocrit Value, Hct"
      - Mcv                     → "Mean Corpuscular Volume, MCV"
      - Mch                     → "Mean Cell Haemoglobin, MCH"
      - Mchc                    → "Mean Cell Haemoglobin CON, MCHC"
    """
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    extracted_data = {}

    # --- Extract Patient Info using regex ---
    for line in lines:
        if line.startswith("Age:"):
            age_match = re.search(r"Age:\s*(\d+(\.\d+)?)", line)
            if age_match:
                extracted_data["Age"] = float(age_match.group(1))
        if line.startswith("Sex:"):
            sex_match = re.search(r"Sex:\s*([MF])", line, re.IGNORECASE)
            if sex_match:
                extracted_data["Sex"] = sex_match.group(1).upper()

    # --- Extract CBC Test Values ---
    cbc_mappings = {
        'Hemoglobin': "Hemoglobin",
        'Leucocyte': "Total Leukocyte Count",
        'Thrombocyte': "Platelet Count",
        'Erythrocyte': "Total RBC Count",
        'Hematocrit': "Hematocrit Value, Hct",
        'Mcv': "Mean Corpuscular Volume, MCV",
        'Mch': "Mean Cell Haemoglobin, MCH",
        'Mchc': "Mean Cell Haemoglobin CON, MCHC"
    }
    
    # Locate the CBC section by finding "COMPLETE BLOOD COUNT"
    start_index = None
    for i, line in enumerate(lines):
        if "COMPLETE BLOOD COUNT" in line.upper():
            start_index = i
            break
    if start_index is None:
        raise ValueError("Could not locate CBC section in the report.")
    
    # Find the table header (e.g., a line containing "TEST")
    table_start = None
    for i in range(start_index, len(lines)):
        if "TEST" in lines[i].upper():
            table_start = i
            break
    if table_start is None:
        raise ValueError("Could not locate CBC table header in the report.")
    
    # For each test, search for its numeric value.
    for i in range(table_start + 1, len(lines)):
        line = lines[i]
        for feature, indicator in cbc_mappings.items():
            if indicator.upper() in line.upper():
                # First try to extract a numeric value from the same line.
                number_match = re.search(r"(\d+(\.\d+)?)", line)
                if number_match:
                    extracted_data[feature] = float(number_match.group(1))
                    continue  # Found the value, move to the next feature.
                # If not found, then scan subsequent lines.
                j = i + 1
                value_found = None
                while j < len(lines):
                    try:
                        candidate = lines[j].replace(",", "")
                        value_candidate = float(candidate)
                        value_found = value_candidate
                        break
                    except ValueError:
                        j += 1
                if value_found is not None:
                    extracted_data[feature] = value_found
                else:
                    raise ValueError(f"Could not extract numeric value for {feature}")
    
    # --- Verify All Required Features ---
    required_features = ['Hemoglobin', 'Leucocyte', 'Thrombocyte', 'Erythrocyte',
                         'Hematocrit', 'Mcv', 'Mch', 'Mchc', 'Age', 'Sex']
    for feat in required_features:
        if feat not in extracted_data:
            raise ValueError(f"Missing required feature: {feat}")
    
    # --- Process Sex Field ---
    sex_val = extracted_data["Sex"]
    if sex_val in ['1', '1.0']:
        extracted_data["Sex"] = 'M'
    elif sex_val in ['0', '0.0']:
        extracted_data["Sex"] = 'F'
    if extracted_data["Sex"] not in ['M', 'F']:
        raise ValueError(f"Invalid value for Sex: {extracted_data['Sex']}. Must be M, F, 1, or 0")
    
    # Build the features list in the order required by the model.
    features = [
        extracted_data['Hematocrit'],
        extracted_data['Hemoglobin'],
        extracted_data['Erythrocyte'],
        extracted_data['Leucocyte'],
        extracted_data['Thrombocyte'],
        extracted_data['Mch'],
        extracted_data['Mchc'],
        extracted_data['Mcv'],
        extracted_data['Age'],
        1 if extracted_data['Sex'] == 'M' else 0
    ]
    
    return features, extracted_data

def analyze_blood_report(features):
    results = {
        'conditions': [],
        'findings': [],
        'treatments': []
    }
    
    if features['Hemoglobin'] < 12 and features['Hematocrit'] < 36:
        if features['Mcv'] < 80:
            results['conditions'].append("Microcytic Anemia")
            results['findings'].append("Low hemoglobin, hematocrit, and MCV suggest iron deficiency anemia")
            results['treatments'].extend([
                "Prescribe iron supplements (ferrous sulfate 325mg oral daily)",
                "Recommend dietary modifications to increase iron-rich foods",
                "Schedule follow-up blood test in 3 months"
            ])
        elif features['Mcv'] > 100:
            results['conditions'].append("Macrocytic Anemia")
            results['findings'].append("Low hemoglobin with high MCV suggests vitamin B12 or folate deficiency")
            results['treatments'].extend([
                "Initiate vitamin B12 injections or oral supplementation",
                "Begin folic acid supplementation",
                "Provide dietary counseling for vitamin B12 and folate-rich foods"
            ])
        else:
            results['conditions'].append("Normocytic Anemia")
            results['findings'].append("Low hemoglobin and hematocrit with normal MCV may indicate acute blood loss or chronic disease")
            results['treatments'].extend([
                "Conduct further evaluation to determine underlying cause",
                "Consider additional tests (iron studies, reticulocyte count, kidney function)"
            ])
    
    if features['Leucocyte'] > 11:
        results['conditions'].append("Leukocytosis")
        results['findings'].append("Elevated white blood cell count indicates possible infection or inflammation")
        results['treatments'].extend([
            "Perform further testing to identify the source of infection",
            "Order a CBC with differential",
            "Consider initiating antibiotic therapy based on clinical findings"
        ])
    
    if features['Thrombocyte'] > 450:
        results['conditions'].append("Thrombocytosis")
        results['findings'].append("High platelet count may be reactive or suggest a myeloproliferative disorder")
        results['treatments'].extend([
            "Repeat platelet count and check inflammatory markers",
            "Evaluate for underlying causes; refer to hematology if persistent"
        ])
    
    if features['Hematocrit'] > 52 and features['Hemoglobin'] > 18:
        results['conditions'].append("Polycythemia")
        results['findings'].append("Elevated hemoglobin and hematocrit may indicate polycythemia vera or secondary polycythemia")
        results['treatments'].extend([
            "Conduct JAK2 mutation analysis",
            "Consider therapeutic phlebotomy",
            "Evaluate need for cytoreductive therapy (e.g., hydroxyurea) in selected cases"
        ])
    
    if features['Mchc'] < 32:
        results['conditions'].append("Hypochromia")
        results['findings'].append("Low MCHC indicates reduced hemoglobin content per cell, common in iron deficiency anemia")
        results['treatments'].extend([
            "Recommend iron supplementation",
            "Advise dietary modifications to boost iron intake",
            "Plan for follow-up evaluation of red cell indices"
        ])
    elif features['Mchc'] > 36:
        results['conditions'].append("Hyperchromia")
        results['findings'].append("Elevated MCHC is unusual and may be seen in conditions like hereditary spherocytosis")
        results['treatments'].extend([
            "Consider osmotic fragility testing",
            "Refer to hematology for further evaluation"
        ])
    
    if features['Age'] > 65:
        results['findings'].append("Patient is elderly; consider age-related changes in blood parameters and higher risk for chronic conditions")
    
    return results

def generate_report(analysis_results, feature_dict):
    report = "BLOOD ANALYSIS REPORT\n\n"
    
    # For unhealthy patients (with conditions)
    if analysis_results['conditions']:
        report += "Status: <span class='text-danger'>Requires Medical Attention</span>\n\n"
        
        report += "Possible Conditions:\n"
        # Add conditions with red highlighting
        for condition in analysis_results['conditions']:
            report += f"• <span class='text-danger'>{condition}</span>\n"
        
        report += "\nDetailed Analysis:\n"
        # Add findings with specific highlighting for medical terms
        for finding in analysis_results['findings']:
            # Highlight specific medical terms and values
            finding = finding.replace("Low ", "<span class='text-danger'>Low</span> ")
            finding = finding.replace("High ", "<span class='text-danger'>High</span> ")
            finding = finding.replace("Elevated ", "<span class='text-danger'>Elevated</span> ")
            finding = finding.replace("hemoglobin", "<span class='text-danger'>hemoglobin</span>")
            finding = finding.replace("hematocrit", "<span class='text-danger'>hematocrit</span>")
            finding = finding.replace("MCV", "<span class='text-danger'>MCV</span>")
            finding = finding.replace("MCHC", "<span class='text-danger'>MCHC</span>")
            finding = finding.replace("white blood cell count", "<span class='text-danger'>white blood cell count</span>")
            finding = finding.replace("platelet count", "<span class='text-danger'>platelet count</span>")
            finding = finding.replace("infection", "<span class='text-danger'>infection</span>")
            finding = finding.replace("inflammation", "<span class='text-danger'>inflammation</span>")
            finding = finding.replace("iron deficiency", "<span class='text-danger'>iron deficiency</span>")
            finding = finding.replace("vitamin B12", "<span class='text-danger'>vitamin B12</span>")
            finding = finding.replace("folate deficiency", "<span class='text-danger'>folate deficiency</span>")
            finding = finding.replace("acute blood loss", "<span class='text-danger'>acute blood loss</span>")
            finding = finding.replace("chronic disease", "<span class='text-danger'>chronic disease</span>")
            finding = finding.replace("myeloproliferative", "<span class='text-danger'>myeloproliferative</span>")
            finding = finding.replace("polycythemia vera", "<span class='text-danger'>polycythemia vera</span>")
            finding = finding.replace("secondary polycythemia", "<span class='text-danger'>secondary polycythemia</span>")
            finding = finding.replace("hereditary spherocytosis", "<span class='text-danger'>hereditary spherocytosis</span>")
            report += f"• {finding}\n"
        
        report += "\nRecommended Actions:\n"
        # Add treatments with key medical terms highlighted
        for treatment in analysis_results['treatments']:
            # Highlight specific medical treatments and tests
            treatment = treatment.replace("iron supplements", "<span class='text-danger'>iron supplements</span>")
            treatment = treatment.replace("ferrous sulfate", "<span class='text-danger'>ferrous sulfate</span>")
            treatment = treatment.replace("vitamin B12", "<span class='text-danger'>vitamin B12</span>")
            treatment = treatment.replace("folic acid", "<span class='text-danger'>folic acid</span>")
            treatment = treatment.replace("antibiotic therapy", "<span class='text-danger'>antibiotic therapy</span>")
            treatment = treatment.replace("CBC", "<span class='text-danger'>CBC</span>")
            treatment = treatment.replace("JAK2 mutation analysis", "<span class='text-danger'>JAK2 mutation analysis</span>")
            treatment = treatment.replace("therapeutic phlebotomy", "<span class='text-danger'>therapeutic phlebotomy</span>")
            treatment = treatment.replace("cytoreductive therapy", "<span class='text-danger'>cytoreductive therapy</span>")
            treatment = treatment.replace("hydroxyurea", "<span class='text-danger'>hydroxyurea</span>")
            treatment = treatment.replace("iron studies", "<span class='text-danger'>iron studies</span>")
            treatment = treatment.replace("reticulocyte count", "<span class='text-danger'>reticulocyte count</span>")
            treatment = treatment.replace("kidney function", "<span class='text-danger'>kidney function</span>")
            treatment = treatment.replace("osmotic fragility testing", "<span class='text-danger'>osmotic fragility testing</span>")
            treatment = treatment.replace("inflammatory markers", "<span class='text-danger'>inflammatory markers</span>")
            report += f"• {treatment}\n"
    
    # For healthy patients (no conditions)
    else:
        report += "Status: <span class='text-success'>Healthy</span>\n\n"
        report += "Possible Conditions:\n"
        report += "• <span class='text-success'>All blood parameters are within normal ranges</span>\n\n"
        report += "Recommendations:\n"
        report += "• Maintain current health status\n"
        report += "• Continue regular <span class='text-success'>exercise</span> and <span class='text-success'>balanced diet</span>\n"
        report += "• Schedule routine follow-up in <span class='text-success'>12 months</span>\n"
    
    # Add a summary of blood parameters with highlighting for abnormal values
    # report += "\nBlood Parameters:\n"
    
    # # Define normal ranges for highlighting
    # normal_ranges = {
    #     'Hemoglobin': {'min': 12, 'max': 18, 'unit': 'g/dL'},
    #     'Hematocrit': {'min': 36, 'max': 52, 'unit': '%'},
    #     'Erythrocyte': {'min': 4, 'max': 6, 'unit': 'M/µL'},
    #     'Leucocyte': {'min': 4, 'max': 11, 'unit': 'K/µL'},
    #     'Thrombocyte': {'min': 150, 'max': 450, 'unit': 'K/µL'},
    #     'Mch': {'min': 27, 'max': 32, 'unit': 'pg'},
    #     'Mchc': {'min': 32, 'max': 36, 'unit': 'g/dL'},
    #     'Mcv': {'min': 80, 'max': 100, 'unit': 'fL'}
    # }
    
    # Add each parameter with appropriate highlighting
    # for param, range_info in normal_ranges.items():
    #     value = feature_dict[param]
    #     unit = range_info['unit']
    #     normal_range = f"{range_info['min']}-{range_info['max']} {unit}"
        
    #     if value < range_info['min'] or value > range_info['max']:
    #         # Abnormal value
    #         value_str = f"<span class='text-danger'>{value} {unit}</span>"
    #         if value < range_info['min']:
    #             status = "<span class='text-danger'>(Low)</span>"
    #         else:
    #             status = "<span class='text-danger'>(High)</span>"
    #     else:
    #         # Normal value
    #         value_str = f"{value} {unit}"
    #         status = "<span class='text-success'>(Normal)</span>"
            
    #     report += f"• {param}: {value_str} {status} [Normal range: {normal_range}]\n"
    
    # Add patient info
    report += f"\nPatient Info:\n"
    report += f"• Age: {feature_dict['Age']} years\n"
    report += f"• Sex: {feature_dict['Sex']}\n"
    
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

        filename_uploaded = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_uploaded)
        file.save(filepath)

        try:
            # Extract features using the new pdfplumber-based function.
            features, extracted_values = extract_features_from_pdf(filepath)
            
            raw_feature_dict = {
                'Hematocrit': float(extracted_values['Hematocrit']),
                'Hemoglobin': float(extracted_values['Hemoglobin']),
                'Erythrocyte': float(extracted_values['Erythrocyte']),
                'Leucocyte': float(extracted_values['Leucocyte']),
                'Thrombocyte': float(extracted_values['Thrombocyte']),
                'Mch': float(extracted_values['Mch']),
                'Mchc': float(extracted_values['Mchc']),
                'Mcv': float(extracted_values['Mcv']),
                'Age': float(extracted_values['Age']),
                'Sex': extracted_values['Sex']
            }

            new_data = pd.DataFrame({
                'HAEMATOCRIT': [raw_feature_dict['Hematocrit']],
                'HAEMOGLOBINS': [raw_feature_dict['Hemoglobin']],
                'ERYTHROCYTE': [raw_feature_dict['Erythrocyte']],
                'LEUCOCYTE': [raw_feature_dict['Leucocyte']],
                'THROMBOCYTE': [raw_feature_dict['Thrombocyte']],
                'MCH': [raw_feature_dict['Mch']],
                'MCHC': [raw_feature_dict['Mchc']],
                'MCV': [raw_feature_dict['Mcv']],
                'AGE': [raw_feature_dict['Age']],
                'SEX': [raw_feature_dict['Sex']]
            })

            new_data_scaled = new_data.copy()
            new_data_scaled['SEX'] = label_encoder_sex.transform(new_data_scaled['SEX'])
            numeric_cols = ['HAEMATOCRIT', 'HAEMOGLOBINS', 'ERYTHROCYTE', 'LEUCOCYTE',
                              'THROMBOCYTE', 'MCH', 'MCHC', 'MCV', 'AGE']
            new_data_scaled[numeric_cols] = scaler.transform(new_data_scaled[numeric_cols])

            prediction = model.predict(new_data_scaled)[0]
            print("Extracted Features:", features)
            print("Prediction:", prediction)

            if prediction == 0:
                analysis = analyze_blood_report(raw_feature_dict)
                detailed_report = generate_report(analysis, raw_feature_dict)
            else:
                detailed_report = generate_report({"conditions": [], "findings": [], "treatments": []}, raw_feature_dict)

            return jsonify({
                "status": "success",
                "prediction": "incare" if prediction == 0 else "outcare",
                "detailed_analysis": detailed_report
            })

        except Exception as e:
            print("Extraction/Predict Error:", str(e))
            return jsonify({"status": "error", "error": str(e)})
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/predict_manual', methods=['POST'])
def predict_manual():
    try:
        data = request.json
        raw_feature_dict = {
            'Hematocrit': float(data['Hematocrit']),
            'Hemoglobin': float(data['Hemoglobin']),
            'Erythrocyte': float(data['Erythrocyte']),
            'Leucocyte': float(data['Leucocyte']),
            'Thrombocyte': float(data['Thrombocyte']),
            'Mch': float(data['Mch']),
            'Mchc': float(data['Mchc']),
            'Mcv': float(data['Mcv']),
            'Age': float(data['Age']),
            'Sex': data['Sex']
        }

        new_data = pd.DataFrame({
            'HAEMATOCRIT': [raw_feature_dict['Hematocrit']],
            'HAEMOGLOBINS': [raw_feature_dict['Hemoglobin']],
            'ERYTHROCYTE': [raw_feature_dict['Erythrocyte']],
            'LEUCOCYTE': [raw_feature_dict['Leucocyte']],
            'THROMBOCYTE': [raw_feature_dict['Thrombocyte']],
            'MCH': [raw_feature_dict['Mch']],
            'MCHC': [raw_feature_dict['Mchc']],
            'MCV': [raw_feature_dict['Mcv']],
            'AGE': [raw_feature_dict['Age']],
            'SEX': [raw_feature_dict['Sex']]
        })

        new_data_scaled = new_data.copy()
        new_data_scaled['SEX'] = label_encoder_sex.transform(new_data_scaled['SEX'])
        numeric_cols = ['HAEMATOCRIT', 'HAEMOGLOBINS', 'ERYTHROCYTE', 'LEUCOCYTE',
                           'THROMBOCYTE', 'MCH', 'MCHC', 'MCV', 'AGE']
        new_data_scaled[numeric_cols] = scaler.transform(new_data_scaled[numeric_cols])

        prediction = model.predict(new_data_scaled)[0]
        print("Manual Prediction:", prediction)

        if prediction == 0:
            analysis = analyze_blood_report(raw_feature_dict)
            detailed_report = generate_report(analysis, raw_feature_dict)
        else:
            detailed_report = generate_report({"conditions": [], "findings": [], "treatments": []}, raw_feature_dict)

        return jsonify({
            "status": "success",
            "prediction": "incare" if prediction == 0 else "outcare",
            "detailed_analysis": detailed_report
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
