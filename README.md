# DocAssist: AI-Powered Medical Decision Support System

## Overview
DocAssist AI-UI is the user interface for the **DocAssist** project, designed to assist doctors in analyzing blood reports using AI-driven insights. This UI allows users to upload PDF or Enter Values of blood test results for automatic processing and interpretation.

## Features
- Upload blood test reports in **PDF** format.
- AI-powered analysis of blood test parameters.
- Intuitive and user-friendly interface.
- Visual representation of test results.
- Secure and efficient processing.

## UI Snapshots
### Main Page
![Main page](https://github.com/user-attachments/assets/2c9c1f29-cff0-42d2-8c4e-abb4a4640fe0)

### Upload PDF Section
![Upload pdf section](https://github.com/user-attachments/assets/7f2676ce-8104-4316-ab48-2b30ce6fa402)

### Enter Values Section
![Enter values Section](https://github.com/user-attachments/assets/e0cfe564-5b14-4f53-81c5-c711ca356d03)

## Installation
**Note:** In `MainApp.js`, update the backend server URL to use the local server: `http://127.0.0.1:5000/` instead of the live backend server.
To run the project locally, follow these steps:

### Prerequisites
Ensure you have the following installed:
- **Node.js** (for frontend development)
- **Python** (for backend API, if applicable)
- **Git** (for cloning the repository)

### Steps
#### Frontend Setup
1. Clone the repository:
   ```sh
   git clone https://github.com/Neo28A/DocAssist_AI-UI.git
   ```
2. Navigate to the frontend directory:
   ```sh
   cd frontend
   ```
3. Install dependencies:
   ```sh
   npm install
   ```
4. Start the development server:
   ```sh
   npm start
   ```
5. Open your browser and navigate to:
   ```
   http://localhost:3000
   ```

#### Backend Setup
1. Navigate to the backend directory:
   ```sh
   cd backend
   ```
2. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the backend server:
   ```sh
   python app.py
   ```

## Usage
1. Upload a **PDF** or **Enter values** of blood report.
2. Let the AI analyze the parameters.
3. View the results and insights.

## Tech Stack
- **Frontend:** React.js
- **Backend:** Python (Flask)
- **Styling:** CSS3

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit changes (`git commit -m 'Added new feature'`).
4. Push to the branch (`git push origin feature-name`).
5. Open a pull request.

## Contact
For any questions or suggestions, feel free to reach out!



