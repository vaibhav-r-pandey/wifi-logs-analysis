#!/usr/bin/env python3
"""
IFX MSD GenAI Tool - Flask Application
AI-powered log analysis for MSD cases
"""

from flask import Flask, render_template, request, redirect, session, flash, jsonify
import markdown
import logs_analysis_genai
import os
import logging
import tempfile
from werkzeug.utils import secure_filename
import test
from datetime import datetime
import uuid
import threading
import time

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

# In-memory job storage
jobs = {}
  
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
 
# Handle WiFi log upload and start async analysis
@app.route('/handle_wifi_upload', methods=['POST'])
def handle_wifi_upload():
    return handle_log_upload('WiFi')

# Handle BT log upload and start async analysis
@app.route('/handle_bt_upload', methods=['POST'])
def handle_bt_upload():
    return handle_log_upload('BT')

# Generic log upload handler
def handle_log_upload(log_type):
    logger.info(f'{log_type} log upload request received')
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
                                 analysis_html=f'<p>Please select a valid {log_type} log file (.log, .txt, .md, .dmesg).</p>',
                                 analysis_type='Error',
                                 timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        filename = secure_filename(file.filename)
        file_content = file.read().decode('utf-8', errors='ignore')
        
        # Start async analysis with log type
        job_id = start_analysis_job(filename, file_content, log_type)
        
        # Return processing page with job ID
        return render_template('processing.html', job_id=job_id, filename=filename)
        
    except Exception as e:
        logger.error(f'Error in {log_type} log upload: {str(e)}')
        return render_template('results.html', 
                             analysis_html=f'<p>Error analyzing {log_type} log file: {str(e)}</p>',
                             analysis_type='Error',
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# Keep the old route for backward compatibility
@app.route('/handle_file_upload', methods=['POST'])
def handle_file_upload():
    return handle_log_upload('WiFi')  # Default to WiFi for backward compatibility

def start_analysis_job(filename, file_content, log_type='WiFi'):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "processing", 
        "result": None, 
        "filename": filename,
        "log_type": log_type,
        "started": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Start background processing
    thread = threading.Thread(target=process_analysis, args=(job_id, filename, file_content, log_type))
    thread.daemon = True
    thread.start()
    
    return job_id

def process_analysis(job_id, filename, file_content, log_type='WiFi'):
    try:
        logger.info(f'Starting background {log_type} analysis for job {job_id}')
        
        # Limit input size
        if len(file_content) > 20000:
            file_content = file_content[-20000:]
        
        # Prepare different prompts based on log type
        if log_type == 'WiFi':
            test_prompt = '''\n\nAnalyze this log file and provide key issues and recommendations'''
        elif log_type == 'BT':
            test_prompt = '''\n\nAnalyze this log file and provide key issues and recommendations'''
        else:
            test_prompt = '\nAnalyze this log file and provide key issues and recommendations.'
        
        analysis_input = file_content + test_prompt
        
        # Get AI analysis
        output = test.test_chat_completion_api(analysis_input)
        
        # Convert to HTML
        html_content = markdown.markdown(output, extensions=['tables', 'fenced_code'])
        
        jobs[job_id] = {
            "status": "complete", 
            "result": html_content, 
            "filename": filename,
            "log_type": log_type,
            "completed": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f'{log_type} analysis completed for job {job_id}')
        
    except Exception as e:
        logger.error(f'{log_type} analysis failed for job {job_id}: {str(e)}')
        jobs[job_id] = {
            "status": "error", 
            "result": f"{log_type} analysis failed: {str(e)}", 
            "filename": filename,
            "log_type": log_type,
            "error": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

@app.route('/job_status/<job_id>')
def job_status(job_id):
    job = jobs.get(job_id, {"status": "not_found"})
    return jsonify(job)

@app.route('/results/<job_id>')
def view_results(job_id):
    job = jobs.get(job_id)
    if not job:
        return render_template('results.html', 
                             analysis_html='<p>Job not found.</p>',
                             analysis_type='Error',
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    if job['status'] == 'complete':
        log_type = job.get('log_type', 'Log')
        return render_template('results.html', 
                             analysis_html=job['result'],
                             analysis_type=f'{log_type} Log Analysis ({job["filename"]})',
                             timestamp=job.get('completed', 'Unknown'))
    else:
        return render_template('results.html', 
                             analysis_html=f'<p>Analysis {job["status"]}: {job.get("result", "Please wait...")}</p>',
                             analysis_type='Status',
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    # No need to create directories - using temp for everything
    # Run in development mode
    app.run(debug=False, host='0.0.0.0', port=5000)
