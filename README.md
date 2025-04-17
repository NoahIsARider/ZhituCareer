# ZhiTuCareer+ Career Analysis System

ZhiTuCareer+ is a web-based career analysis and job recommendation system that helps users analyze their career path and find suitable job opportunities based on their profile.

## Features

- Career path analysis based on user profile
- Job recommendations based on skills and experience
- Market trend analysis
- Job search functionality

## Prerequisites

- [Anaconda](https://www.anaconda.com/download) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- Python 3.9 or higher

## Installation and Setup

### 1. Create and Activate Conda Environment

```bash
# Create a new conda environment
conda create -n zhitu_career python=3.9

# Activate the environment
conda activate zhitu_career
```

### 2. Clone the Repository

```bash
# Clone the repository to your local machine
git clone <repository-url>
cd ZhiTuCareer+
```

### 3. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Create a `.env` file in the project root directory
2. Add your ModelScope API key:
```
OPENAI_API_KEY=your_modelscope_api_key
```

## Running the Application

1. Make sure you are in the project directory and your conda environment is activated:
```bash
conda activate zhitucareer
```

2. Start the Flask application:
```bash
python app.py
```

3. Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Fill in your profile information in the web interface:
   - Education background
   - Major/Field of study
   - Skills
   - Work experience
   - Career goals

2. Click "获取职业分析" to receive career analysis and recommendations

3. Use the job search function to find specific positions based on keywords and location

## Troubleshooting

- If you encounter any package installation issues, try updating pip:
  ```bash
  python -m pip install --upgrade pip
  ```

- If the application fails to start, check that:
  - The conda environment is activated
  - All dependencies are installed
  - The .env file is properly configured
  - Port 5000 is not in use by another application

## License

This project is licensed under the MIT License - see the LICENSE file for details.