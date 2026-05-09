import os
import subprocess
from datetime import datetime



# Set the start time of the entire process
start_time = datetime.now()
cwd = os.getcwd()

# Change directories to cwd
os.chdir(cwd)
cwd = os.getcwd()
print(f'Working directory: {cwd}')

script_path = 'C:\\Users\\mas58\\PycharmProjects\\Trading\\_main_.py'

# paths for stderr and stdout files
outfiles = {
    'stderr': cwd + '\\log_files\\' + str(start_time.strftime('%Y-%m-%d %H-%M-%S')) + '_stderr.txt',
    'stdout': cwd + '\\log_files\\' + str(start_time.strftime('%Y-%m-%d %H-%M-%S')) + '_stdout.txt',
}

# Get Environment Attributes
env = os.environ.copy()

try:
    command = f'python {script_path}'
    print(f'Running command: {command}')

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

    print('Command Submitted Successfully \n')

    try:
        output, errs = proc.communicate(timeout=10 * 60)
    except subprocess.TimeoutExpired:
        proc.kill()
        output, errs = proc.communicate()

    if not os.path.isdir(cwd + '\\log_files'):
        os.mkdir(cwd + '\\log_files')

    with open(outfiles['stderr'], 'w') as f:
        for line in errs.decode():
            f.write(line)

    with open(outfiles['stdout'], 'w') as f:
        for line in output.decode():
            f.write(line)

    status_desc = {
        'RAN TO COMPLETION': 'No Error stopped the process prematurely.',
        'WARNINGS/ERRORS PRESENT': 'There were warnings or errors thrown during runtime. Check stderr.txt.'
    }

    status = 'RAN TO COMPLETION'
    with open(cwd + '\\log_files\\' + str(start_time.strftime('%Y-%m-%d %H-%M-%S')) + '_stderr.txt', 'r') as f:
        counter = 0
        for line in f:
            status = 'WARNINGS/ERRORS PRESENT'
            break

    print(status)
except:
    print('Something went wrong...')
    raise

# Email stderr and stdout

print('Done!')