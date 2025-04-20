# ZhiTuCareer+ Career Analysis System

ZhiTuCareer+ is a web-based career analysis and job recommendation system that helps users analyze their career path and find suitable job opportunities based on their profile. The system leverages advanced AI technology to provide personalized career guidance and job matching services.

## Features

- **Career Path Analysis**: Detailed analysis based on user's professional profile
- **Job Recommendations**: Personalized job suggestions based on skills and experience
- **Market Trend Analysis**: Insights into current industry and job market trends
- **Job Search Functionality**: Advanced search tools to find relevant positions
- **Course Recommendations**: Educational resources aligned with career goals

## Prerequisites

Before you begin, ensure you have the following installed:

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
git clone [repository-url]
cd ZhiTuCareer+
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory and add your ModelScope API key:

```env
# ModelScope API配置 (使用OpenAI客户端)
OPENAI_API_KEY=your_api_key_here
```

## Running the Application

1. Make sure you are in the project directory and your conda environment is activated:
```bash
conda activate zhitu_career
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

4. Review recommended courses and learning paths aligned with your career goals

## System Architecture

ZhiTuCareer+ is built with a modular architecture:

- **User Profile Agent**: Handles user information processing
- **Job Matching Agent**: Processes job recommendations
- **Market Analysis Agent**: Analyzes market trends
- **Course Matching Agent**: Suggests relevant courses

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.