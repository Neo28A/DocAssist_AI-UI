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

backend_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(backend_dir, "xgboost_model.sav")
scaler_path = os.path.join(backend_dir, "scaler.pkl")
label_encoder_sex_path = os.path.join(backend_dir, "label_encoder_sex.pkl")

try:
    model = pickle.load(open(model_path, 'rb'))
    scaler = pickle.load(open(scaler_path, 'rb'))
    label_encoder_sex = pickle.load(open(label_encoder_sex_path, 'rb'))
    print("Global objects loaded successfully!")
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
                        normalized_data[feature] = value
                        break
                if value is None:
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
    # Your analysis logic here...
    results = {
        'conditions': [],
        'findings': [],
        'treatments': []
    }
    if features['Hemoglobin'] < 12 and features['Hematocrit'] < 36:
        if features['Mcv'] < 80:
            results['conditions'].append("Microcytic Anemia")
            results['findings'].append("Low hemoglobin, hematocrit, and MCV indicate iron deficiency anemia")
            results['treatments'].extend([
                "Prescribe iron supplements (ferrous sulfate 325mg oral daily)",
                "Dietary modifications: increase iron-rich foods",
                "Follow-up blood test in 3 months"
            ])
        elif features['Mcv'] > 100:
            results['conditions'].append("Macrocytic Anemia")
            results['findings'].append("Low hemoglobin with high MCV suggests vitamin B12 or folate deficiency")
            results['treatments'].extend([
                "Vitamin B12 injections or oral supplements",
                "Folic acid supplementation",
                "Dietary counseling for B12 and folate-rich foods"
            ])
    if features['Leucocyte'] > 11:
        results['conditions'].append("Leukocytosis")
        results['findings'].append("Elevated white blood cell count indicates possible infection or inflammation")
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
            report += f"• <span class='text-danger'>{finding}</span>\n"
        report += "\nTreatment Recommendations:\n"
        for treatment in analysis_results['treatments']:
            report += f"• {treatment}\n"
    else:
        report += "Identified Conditions:\n• <span class='text-success'>No abnormal conditions detected</span>\n\n"
        report += "Clinical Findings:\n• <span class='text-success'>All blood parameters are within normal ranges</span>\n\n"
        report += "Treatment Recommendations:\n• Maintain current health status\n• Continue regular exercise and balanced diet\n• Schedule routine follow-up in 12 months\n"
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

            # Use the loaded label encoder and scaler to transform the data
            new_data['SEX'] = label_encoder_sex.transform(new_data['SEX'])
            numeric_cols_new = ['HAEMATOCRIT', 'HAEMOGLOBINS', 'ERYTHROCYTE', 'LEUCOCYTE',
                                'THROMBOCYTE', 'MCH', 'MCHC', 'MCV', 'AGE']
            new_data[numeric_cols_new] = scaler.transform(new_data[numeric_cols_new])

            prediction = model.predict(new_data)[0]
            print("Extracted Features:", features)
            print("Prediction:", prediction)

            if prediction == 0:
                analysis = analyze_blood_report(raw_feature_dict)
                detailed_report = generate_report(analysis, raw_feature_dict)
            else:
                detailed_report = generate_report({"conditions": [], "findings": [], "treatments": []}, raw_feature_dict)

            return jsonify({
                "status": "success",
                "prediction": "in" if prediction == 0 else "out",
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

        new_data = pd.DataFrame({
            'HAEMATOCRIT': [float(data['Hematocrit'])],
            'HAEMOGLOBINS': [float(data['Hemoglobin'])],
            'ERYTHROCYTE': [float(data['Erythrocyte'])],
            'LEUCOCYTE': [float(data['Leucocyte'])],
            'THROMBOCYTE': [float(data['Thrombocyte'])],
            'MCH': [float(data['Mch'])],
            'MCHC': [float(data['Mchc'])],
            'MCV': [float(data['Mcv'])],
            'AGE': [float(data['Age'])],
            'SEX': [data['Sex']]
        })

        # Use the loaded label encoder and scaler
        new_data['SEX'] = label_encoder_sex.transform(new_data['SEX'])
        numeric_cols_new = ['HAEMATOCRIT', 'HAEMOGLOBINS', 'ERYTHROCYTE', 'LEUCOCYTE',
                            'THROMBOCYTE', 'MCH', 'MCHC', 'MCV', 'AGE']
        new_data[numeric_cols_new] = scaler.transform(new_data[numeric_cols_new])

        prediction = model.predict(new_data)[0]
        print("Manual Prediction:", prediction)

        feature_dict = {
            'Hematocrit': new_data['HAEMATOCRIT'].iloc[0],
            'Hemoglobin': new_data['HAEMOGLOBINS'].iloc[0],
            'Erythrocyte': new_data['ERYTHROCYTE'].iloc[0],
            'Leucocyte': new_data['LEUCOCYTE'].iloc[0],
            'Thrombocyte': new_data['THROMBOCYTE'].iloc[0],
            'Mch': new_data['MCH'].iloc[0],
            'Mchc': new_data['MCHC'].iloc[0],
            'Mcv': new_data['MCV'].iloc[0],
            'Age': new_data['AGE'].iloc[0],
            'Sex': new_data['SEX'].iloc[0]
        }

        if prediction == 0:
            analysis = analyze_blood_report(feature_dict)
            detailed_report = generate_report(analysis, feature_dict)
        else:
            detailed_report = generate_report({"conditions": [], "findings": [], "treatments": []}, feature_dict)

        return jsonify({
            "status": "success",
            "prediction": "in" if prediction == 0 else "out",
            "detailed_analysis": detailed_report
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
