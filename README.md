# ZhiTuCareer+ Career Analysis System

ZhiTuCareer+ is a comprehensive web-based platform designed to assist users in analyzing their career paths and finding suitable job opportunities. By leveraging advanced AI technology, the system offers personalized career guidance and job matching services, ensuring users receive tailored recommendations based on their unique profiles.

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

## Deployment Instructions

### Prerequisites

Ensure you have the following installed:
- [Anaconda](https://www.anaconda.com/download) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- Python 3.9 or higher

### Step-by-Step Setup

1. **Create and Activate Conda Environment**
   ```bash
   conda create -n zhitu_career python=3.12
   conda activate zhitu_career
   ```

2. **Clone the Repository**
   ```bash
   git clone [repository-url]
   cd ZhiTuCareer+
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   Create a `.env` file in the project root directory and add your ModelScope API key:
   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

5. **Run the Application**
   - Ensure your conda environment is activated:
     ```bash
     conda activate zhitu_career
     ```
   - Start the Flask application:
     ```bash
     python app.py
     ```
   - Access the application at:
     ```
     http://localhost:5000
     ```

## UI Guide for Administrators and Users

### Administrator Usage

Administrators can manage courses and jobs through the admin interface. This includes adding, updating, and removing entries. To access the admin interface, navigate to the admin.html page and log in with your administrator credentials.

### User Identity Information

Users should store their identity information in the users.json file located in the data directory. This includes details such as name, email, and role. Proper role assignment is crucial for access control within the system.
- **Monitoring User Activity**: Track user interactions and gather insights to improve the platform.

### User Guide
- **Profile Setup**: Users should fill in their educational background, skills, work experience, and career goals.
- **Career Analysis**: Click "获取职业分析" to receive personalized career analysis and job recommendations.
- **Job Search**: Utilize the search function to find jobs based on keywords and location.
- **Course Recommendations**: Explore suggested courses and learning paths aligned with career objectives.

## Core Concept: Integrating Agents with Playwright

ZhiTuCareer+ employs a modular architecture where agents are integrated with Playwright for enhanced market analysis and job recommendations.

- **User Profile Agent**: Handles user information processing, ensuring that user profiles are accurately maintained and updated.
- **Job Matching Agent**: Processes job recommendations by analyzing user profiles and matching them with suitable job opportunities.
- **Market Analysis Agent**: Utilizes Playwright to scrape and analyze market trends, providing real-time insights that inform job recommendations and career advice.
- **Course Matching Agent**: Suggests relevant courses and educational resources aligned with user career goals, enhancing skill development.
- **Job Recommendation Agent**: Leverages AI to match user profiles with suitable job opportunities, ensuring personalized job suggestions.

This integration allows for dynamic data collection and processing, ensuring users receive the most relevant and up-to-date information.
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
