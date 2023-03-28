import dxpy

# Set your DNAnexus API token
dxpy.set_security_context({"auth_token_type": "Bearer", "auth_token": "wWPpJGA9jPho4RjpOuzrGBAktQXCzVHf"})

# Specify the run folder name and project ID
run_folder = '220725_A01184_0145_BH375JDRX2'
project_id = 'project-G20fJgQ4V6pqf5GqFF4ZZfGV'

# Search for all folders in the project
for analysis in dxpy.find_analyses(project=project_id, no_parent_job=True, include_subjobs=False, created_after="-1w"):
    analysis_desc = dxpy.DXAnalysis(analysis['id']).describe()
    print(analysis_desc['folder'])
    if run_folder in str(analysis_desc['folder']):
        print(analysis_desc['state'], analysis_desc['id'])