import dxpy
import time

# Set your DNAnexus API token
dxpy.set_security_context({"auth_token_type": "Bearer", "auth_token": "wWPpJGA9jPho4RjpOuzrGBAktQXCzVHf"})

# Specify the run folder name
run_folder = '220725_A01184_0145_BH375JDRX2'
project_id = 'project-G20fB684yYBbqfXFBvGvzgXV'

# Search for all jobs in the project
for job in dxpy.find_jobs(project=project_id):
    # Retrieve the job description
    job_desc = dxpy.DXJob(job['id']).describe()
    if run_folder in str(job_desc['folder']):
        print("Job ID:", job_desc['id'], " Status:", job_desc['state'])
