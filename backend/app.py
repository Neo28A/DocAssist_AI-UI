from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from werkzeug.utils import secure_filename
import os
import PyPDF2
import pickle
import pandas as pd
from sklearn.preprocessing import LabelEncoder, RobustScaler

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load global objects (model, scaler, and label encoder)

# ... existing imports ...

# Update the model paths to point to the models folder
backend_dir = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(backend_dir, "models")
model_path = os.path.join(models_dir, "xgboost_model.sav")
scaler_path = os.path.join(models_dir, "scaler.pkl")
label_encoder_sex_path = os.path.join(models_dir, "label_encoder_sex.pkl")

# Ensure models directory exists
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
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    lines = text.split('\n')
    header_line = None
    data_line = None
    for line in lines:
        if "hematocrit" in line.lower() and "sex" in line.lower():
            header_line = line
        elif header_line and any(char.isdigit() for char in line):
            data_line = line
            break
    if header_line and data_line:
        headers = header_line.split()
        values = data_line.split()
        if len(headers) == len(values):
            extracted_data = {}
            for header, value in zip(headers, values):
                extracted_data[header.upper()] = value
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
            features = []
            normalized_data = {}
            for feature, aliases in feature_mappings.items():
                value = None
                for alias in aliases:
                    if alias in extracted_data:
                        value = extracted_data[alias]
                        # Special handling for Sex field
                        if feature == 'Sex':
                            # Convert numeric values to M/F
                            if value in ['1', '1.0']:
                                value = 'M'
                            elif value in ['0', '0.0']:
                                value = 'F'
                            # Validate M/F values
                            if value not in ['M', 'F']:
                                raise ValueError(f"Invalid value for Sex: {value}. Must be M, F, 1, or 0")
                            features.append(1 if value == 'M' else 0)  # Convert back to numeric for model
                        else:
                            try:
                                features.append(float(value))
                            except ValueError:
                                raise ValueError(f"Invalid value for {feature}: {value}")
                        normalized_data[feature] = value
                        break
                if value is None:
                    raise ValueError(f"Missing required feature: {feature}")
            return features, normalized_data
        else:
            raise ValueError("Mismatch between header and data columns.")
    else:
        raise ValueError("Could not locate headers or data in the PDF.")

def analyze_blood_report(features):
    # Rule-based treatment recommendation system
    results = {
        'conditions': [],
        'findings': [],
        'treatments': []
    }
    
    # Anemia evaluation
    if features['Hemoglobin'] < 12 and features['Hematocrit'] < 36:
        # Microcytic anemia
        if features['Mcv'] < 80:
            results['conditions'].append("Microcytic Anemia")
            results['findings'].append("Low hemoglobin, hematocrit, and MCV suggest iron deficiency anemia")
            results['treatments'].extend([
                "Prescribe iron supplements (ferrous sulfate 325mg oral daily)",
                "Recommend dietary modifications to increase iron-rich foods",
                "Schedule follow-up blood test in 3 months"
            ])
        # Macrocytic anemia
        elif features['Mcv'] > 100:
            results['conditions'].append("Macrocytic Anemia")
            results['findings'].append("Low hemoglobin with high MCV suggests vitamin B12 or folate deficiency")
            results['treatments'].extend([
                "Initiate vitamin B12 injections or oral supplementation",
                "Begin folic acid supplementation",
                "Provide dietary counseling for vitamin B12 and folate-rich foods"
            ])
        else:
            # Normocytic anemia
            results['conditions'].append("Normocytic Anemia")
            results['findings'].append("Low hemoglobin and hematocrit with normal MCV may indicate acute blood loss or chronic disease")
            results['treatments'].extend([
                "Conduct further evaluation to determine underlying cause",
                "Consider additional tests (iron studies, reticulocyte count, kidney function)"
            ])
    
    # Leukocytosis evaluation
    if features['Leucocyte'] > 11:
        results['conditions'].append("Leukocytosis")
        results['findings'].append("Elevated white blood cell count indicates possible infection or inflammation")
        results['treatments'].extend([
            "Perform further testing to identify the source of infection",
            "Order a CBC with differential",
            "Consider initiating antibiotic therapy based on clinical findings"
        ])
    
    # Thrombocytosis evaluation
    if features['Thrombocyte'] > 450:
        results['conditions'].append("Thrombocytosis")
        results['findings'].append("High platelet count may be reactive or suggest a myeloproliferative disorder")
        results['treatments'].extend([
            "Repeat platelet count and check inflammatory markers",
            "Evaluate for underlying causes; refer to hematology if persistent"
        ])
    
    # Polycythemia evaluation
    if features['Hematocrit'] > 52 and features['Hemoglobin'] > 18:
        results['conditions'].append("Polycythemia")
        results['findings'].append("Elevated hemoglobin and hematocrit may indicate polycythemia vera or secondary polycythemia")
        results['treatments'].extend([
            "Conduct JAK2 mutation analysis",
            "Consider therapeutic phlebotomy",
            "Evaluate need for cytoreductive therapy (e.g., hydroxyurea) in selected cases"
        ])
    
    # MCHC-based red cell evaluation
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
    
    # Age-related note
    if features['Age'] > 65:
        results['findings'].append("Patient is elderly; consider age-related changes in blood parameters and higher risk for chronic conditions")
    
    return results

def generate_report(analysis_results, feature_dict):
    report = "BLOOD ANALYSIS REPORT\n\n"
    
    # For unhealthy patients (with conditions)
    if analysis_results['conditions']:
        # report += "Status: <span class='text-danger'>Requires Medical Attention</span>\n\n"
        
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
            report += f"• {finding}\n"
        
        report += "\nRecommended Actions:\n"
        # Add treatments with key medical terms highlighted
        for treatment in analysis_results['treatments']:
            # Highlight specific medical treatments and tests
            treatment = treatment.replace("iron supplements", "<span class='text-danger'>iron supplements</span>")
            treatment = treatment.replace("vitamin B12", "<span class='text-danger'>vitamin B12</span>")
            treatment = treatment.replace("folic acid", "<span class='text-danger'>folic acid</span>")
            treatment = treatment.replace("antibiotic therapy", "<span class='text-danger'>antibiotic therapy</span>")
            treatment = treatment.replace("CBC", "<span class='text-danger'>CBC</span>")
            treatment = treatment.replace("JAK2 mutation analysis", "<span class='text-danger'>JAK2 mutation analysis</span>")
            treatment = treatment.replace("therapeutic phlebotomy", "<span class='text-danger'>therapeutic phlebotomy</span>")
            report += f"• {treatment}\n"
    
    # For healthy patients (no conditions)
    else:
        report += "Status: <span class='text-success'>Healthy</span>\n\n"
        report += "Possible Conditions:\n"
        report += "• <span class='text-success'>All blood parameters are within normal ranges</span>\n\n"
        report += "Recommendations:\n"
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

        filename_uploaded = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_uploaded)
        file.save(filepath)

        try:
            features, extracted_values = extract_features_from_pdf(filepath)
            # Create a raw feature dictionary for report generation
            raw_feature_dict = {
                'Hematocrit': float(features[0]),
                'Hemoglobin': float(features[1]),
                'Erythrocyte': float(features[2]),
                'Leucocyte': float(features[3]),
                'Thrombocyte': float(features[4]),
                'Mch': float(features[5]),
                'Mchc': float(features[6]),
                'Mcv': float(features[7]),
                'Age': float(features[8]),
                'Sex': extracted_values['Sex']
            }

            # Prepare a DataFrame for prediction
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

            # Scale data for prediction only
            new_data_scaled = new_data.copy()
            new_data_scaled['SEX'] = label_encoder_sex.transform(new_data_scaled['SEX'])
            numeric_cols_new = ['HAEMATOCRIT', 'HAEMOGLOBINS', 'ERYTHROCYTE', 'LEUCOCYTE',
                              'THROMBOCYTE', 'MCH', 'MCHC', 'MCV', 'AGE']
            new_data_scaled[numeric_cols_new] = scaler.transform(new_data_scaled[numeric_cols_new])

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
        
        # Store raw data for analysis
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

        # Create DataFrame for prediction
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

        # Scale data for prediction only
        new_data_scaled = new_data.copy()
        new_data_scaled['SEX'] = label_encoder_sex.transform(new_data_scaled['SEX'])
        numeric_cols_new = ['HAEMATOCRIT', 'HAEMOGLOBINS', 'ERYTHROCYTE', 'LEUCOCYTE',
                           'THROMBOCYTE', 'MCH', 'MCHC', 'MCV', 'AGE']
        new_data_scaled[numeric_cols_new] = scaler.transform(new_data_scaled[numeric_cols_new])

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
