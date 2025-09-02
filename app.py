#!/usr/bin/env python3
"""
IFX MSD GenAI Tool - Flask Application
AI-powered log analysis for MSD cases
"""

from flask import Flask, render_template, request, redirect, session, flash
import markdown
import logs_analysis_genai
import os
import logging
import tempfile
from werkzeug.utils import secure_filename
import test
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()  # Use system temp directory

# Allowed file extensions
ALLOWED_EXTENSIONS = {'log', 'txt', 'md', 'dmesg'}
  
# To render a Index Page 
@app.route('/')
def view_form():
    return render_template('index.html')
  
# For handling post request form we can get the form
# inputs value by using POST attribute.
# this values after submitting you will never see in the urls.
@app.route('/handle_post', methods=['POST'])
def handle_post():
    try:
        msdcaseurl = request.form.get('MSDURL', '').strip()
        
        if not msdcaseurl:
            logger.warning('Empty MSD URL provided')
            return render_template('results.html', 
                                 analysis_html='<p>Please provide a valid MSD case URL.</p>',
                                 analysis_type='Error',
                                 timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        logger.info(f'Processing MSD URL: {msdcaseurl}')
        
        # Run analysis
        analysis = logs_analysis_genai.run_analysis(msdcaseurl)
        
        # Read the analysis results
        try:
            with open('response.md', 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Backup the response to temp directory
            try:
                response_file = os.path.join(tempfile.gettempdir(), f'response_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')
                with open(response_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                logger.info(f'Response saved to: {response_file}')
            except:
                logger.warning('Could not save response file - continuing without saving')
                
        except FileNotFoundError:
            logger.error('Response file not found')
            return render_template('results.html', 
                                 analysis_html='<p>Analysis completed but results file not found.</p>',
                                 analysis_type='Error',
                                 timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Convert to HTML
        html_content = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])
        
        logger.info('MSD analysis completed successfully')
        return render_template('results.html', 
                             analysis_html=html_content,
                             analysis_type='MSD Case Analysis',
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
    except Exception as e:
        logger.error(f'Error in MSD analysis: {str(e)}')
        return render_template('results.html', 
                             analysis_html=f'<p>Error processing MSD case: {str(e)}</p>',
                             analysis_type='Error',
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
 
# Handle file upload and analysis
@app.route('/handle_file_upload', methods=['POST'])
def handle_file_upload():
    logger.info('File upload request received')
    try:
        if 'logfile' not in request.files:
            logger.warning('No file in request')
            return render_template('results.html', 
                                 analysis_html='<p>No file was selected for upload.</p>',
                                 analysis_type='Error',
                                 timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        file = request.files['logfile']
        if file.filename == '' or not allowed_file(file.filename):
            logger.warning(f'Invalid file: {file.filename}')
            return render_template('results.html', 
                                 analysis_html='<p>Please select a valid log file (.log, .txt, .md, .dmesg).</p>',
                                 analysis_type='Error',
                                 timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        filename = secure_filename(file.filename)
        
        # Use temporary file to avoid permission issues
        with tempfile.NamedTemporaryFile(mode='w+', suffix=f'_{filename}', delete=False) as temp_file:
            # Save file content to temp file
            file_content = file.read().decode('utf-8', errors='ignore')
            temp_file.write(file_content)
            temp_filepath = temp_file.name
        
        logger.info(f'File uploaded to temp: {filename}')
        
        # Limit input size to prevent timeouts
        if len(file_content) > 20000:
            file_content = file_content[-20000:]  # Keep last 20k chars
            logger.info('Large file truncated to prevent timeout')
        
        # Prepare prompt for analysis
        test_prompt = '\nAnalyze this log file and provide key issues and recommendations.'
        analysis_input = file_content + test_prompt
        
        # Get analysis from AI with timeout protection
        logger.info('Starting AI analysis')
        try:
            output = test.test_chat_completion_api(analysis_input)
            logger.info('AI analysis completed successfully')
        except Exception as ai_error:
            logger.error(f'AI analysis failed: {str(ai_error)}')
            # Provide basic analysis as fallback
            output = f"""# Log Analysis Results

**Status:** Analysis service temporarily unavailable

**File:** {filename}
**Size:** {len(file_content)} characters

## Basic Information
- File processed successfully
- Content extracted and ready for analysis
- Please try again later or contact support

**Error Details:** {str(ai_error)}
"""
        
        # Save analysis to temp file (optional - for debugging)
        try:
            analysis_file = os.path.join(tempfile.gettempdir(), f'file_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')
            with open(analysis_file, 'w', encoding='utf-8') as f:
                f.write(output)
            logger.info(f'Analysis saved to: {analysis_file}')
        except:
            logger.warning('Could not save analysis file - continuing without saving')
        
        # Convert to HTML
        html_content = markdown.markdown(output, extensions=['tables', 'fenced_code'])
        
        # Clean up temp file
        try:
            os.remove(temp_filepath)
        except:
            pass  # Ignore cleanup errors
        logger.info(f'Analysis completed for: {filename}')
        
        return render_template('results.html', 
                             analysis_html=html_content,
                             analysis_type=f'File Analysis ({filename})',
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
    except Exception as e:
        logger.error(f'Error in file upload: {str(e)}')
        return render_template('results.html', 
                             analysis_html=f'<p>Error analyzing file: {str(e)}</p>',
                             analysis_type='Error',
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    # No need to create directories - using temp for everything
    # Run in development mode
    app.run(debug=False, host='0.0.0.0', port=5000)
