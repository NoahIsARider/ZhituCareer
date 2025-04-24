# ZhiTuCareer+ Career Analysis System

ZhiTuCareer+ is a comprehensive web-based platform designed to assist users in analyzing their career paths and finding suitable job opportunities. By leveraging advanced AI technology, the system offers personalized career guidance and job matching services, ensuring users receive tailored recommendations based on their unique profiles.

## Features

- **Career Path Analysis**: Detailed analysis based on user's professional profile
- **Job Recommendations**: Personalized job suggestions based on skills and experience
- **Market Trend Analysis**: Insights into current industry and job market trends
- **Job Search Functionality**: Advanced search tools to find relevant positions
- **Course Recommendations**: Educational resources aligned with career goals


## Deployment Instructions

### Prerequisites

Ensure you have the following installed:
- [Anaconda](https://www.anaconda.com/download) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- Python 3.9 or higher

### Step-by-Step Setup

1. **Create and Activate Conda Environment**
   ```bash
   conda create -n zhitu_career python=3.9
   ```

   ```bash
   conda activate zhitu_career
   ```

2. **Clone the Repository**
   ```bash
   git clone https://github.com/NoahIsARider/ZhituCareer.git
   ```

   ```bash
   cd ZhituCareer
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**

   Create a `.env` file in the project root directory and add your [ModelScope](https://www.modelscope.cn/) API key(silicon should be working just fine as well):
   ```env
   OPENAI_API_KEY=your_api_key_here
   ```
   Change your model name for each module python file in the root directory
6. **Run the Application**
 
   Ensure your conda environment is activated:
     ```bash
     conda activate zhitu_career
     ```
   Start the Flask application:
     ```bash
     python app.py
     ```
   Access the application at:
     ```
     http://localhost:5000
     ```
![image](https://github.com/user-attachments/assets/8db2bbd8-1cec-4345-af3a-7efe65da5429)


## UI Guide for Administrators and Users

### User Identity Information

Users should store their identity information in the users.json file located in the data directory. This includes details such as name, email, and role. Proper role assignment is crucial for access control within the system.
- **Monitoring User Activity**: Track user interactions and gather insights to improve the platform.

![image](https://github.com/user-attachments/assets/b6b6d3c1-95ab-4eb3-955f-41190710846c)


### Administrator Usage

Administrators can manage courses and jobs through the admin interface. This includes adding, updating, and removing entries. To access the admin interface, navigate to the admin.html page and log in with your administrator credentials. Drop your data in the data/jobs.json or data/course.json file or through the UI. Maybe incorporate the project with your database, which should be easy, I guess(check out the [data_base branch](https://github.com/NoahIsARider/ZhituCareer/tree/data_base)).

<img width="1280" alt="image" src="https://github.com/user-attachments/assets/2118c453-ac3c-4d99-ab1a-e52755b06a24" />

### User Guide
1. Fill in your profile information in the web interface:
   - Education background
   - Major/Field of study
   - Skills
   - Work experience
   - Career goals

2. Click "获取职业分析" to receive career analysis and recommendations

![image](https://github.com/user-attachments/assets/57730262-2676-4f0a-bca1-ce4e2a590af6)

3. Use the job search function to find specific positions based on keywords and location

![image](https://github.com/user-attachments/assets/8c754877-60c6-418b-a5ee-0adbea9c5a24)

4. Review recommended courses and learning paths aligned with your career goals

![image](https://github.com/user-attachments/assets/4f7ea2c5-87d8-43b3-97c5-a55bd302448b)

### Substitution

The index_colorblind provides a simple neat UI simply for regular users. Try it!

## Core Concept: Integrating Agents with Playwright

ZhiTuCareer+ employs a modular architecture where agents are integrated with [Playwright](https://playwright.dev/docs/intro) for enhanced market analysis and job recommendations.

- **User Profile Agent**: Handles user information processing, ensuring that user profiles are accurately maintained and updated.
- **Job Matching Agent**: Processes job recommendations by analyzing user profiles and matching them with suitable job opportunities.
- **Market Analysis Agent**: Utilizes Playwright to scrape and analyze market trends, providing real-time insights that inform job recommendations and career advice.
- **Course Matching Agent**: Suggests relevant courses and educational resources aligned with user career goals, enhancing skill development.
- **Job Recommendation Agent**: Leverages AI to match user profiles with suitable job opportunities, ensuring personalized job suggestions.



This integration allows for dynamic data collection and processing, ensuring users receive the most relevant and up-to-date information.




## System Architecture

- **User Profile Agent**: Handles user information processing
- **Market Analysis Agent**: Analyzes market trends
- **Career Advice Agent**: Provide comprehensive career advices
- **Job Matching Agent**: Processes job recommendations
- **Course Matching Agent**: Suggests relevant courses
<div align=center>
   
<img src="https://github.com/NoahIsARider/ZhituCareer/blob/main/agent/agent_structure.jpeg" width="350px">

</div>

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


## License

This project is licensed under the MIT License - see the LICENSE file for details.
