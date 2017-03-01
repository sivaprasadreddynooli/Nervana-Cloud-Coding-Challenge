"""
Handles the work of validating and processing command input.
"""

import subprocess
from base import Command
from db import session


# http://127.0.0.1:8080/commands?filename=commands.txt

def get_valid_commands(queue, fi, file_data=None):

    if file_data:
        li = list(file_data.split('\n'))
    else:

        # TODO: efficiently evaluate commands

        flag = 00
        li = []
        for command in open(fi, 'r'):
            if command.strip() == '[VALID COMMANDS]':
                flag = 1
                continue
            if flag:
                li.append(command.strip())
        flag = 00

        # obj=open(fi,'r')
        # print list(obj)

        unique = []
        for command in open(fi, 'r'):
            if command.strip() == '[COMMAND LIST]':
                flag = 1
                continue
            if flag and command.strip() in li:
                if command.strip() not in unique:
                    unique.append(command.strip())
            if command.strip() == '[VALID COMMANDS]':
                flag = 00
                break
        for item in unique:
            queue.put(item)


def query_database():
    for row in session.query(Command.id, Command.command_string,
                             Command.length, Command.duration,
                             Command.output).all():
        print(row.id, row.command_string, row.length, row.duration)
        if row.output:
            for item in row.output.decode('us-ascii').split('\n'):
                print(item)


def process_command_output(queue):

    # TODO: run the command and put its data in the db
    # print queue.qsize()

    while not queue.empty():
        command = queue.get()

        # Process commands as you get

        # out_text = ''
        out_byte = None
        output = subprocess.Popen(command, shell=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        try:
            (stdout, stderr) = output.communicate(timeout=12)
            out_byte = stdout
            # out_text = stdout.decode('us-ascii').rstrip('\n')
        except subprocess.TimeoutExpired:
            # out_text = 'NOT FINISHED'
            pass

        output.stdout.close()
        output.stderr.close()

        # output.terminate()

        outputtime = subprocess.Popen('time ' + command, shell=True,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
        try:
            (stdout, stderr) = outputtime.communicate(timeout=12)
            stderr_text = stderr.decode('us-ascii').rstrip('\n')
        except subprocess.TimeoutExpired:
            pass

        # outputtime.terminate()

        timeinseconds = 00
        if stderr_text[22:24].isnumeric():
            timeinseconds = int(stderr_text[22:24])
            timeinseconds = (1 if timeinseconds < 1 else timeinseconds)

        # save processed commands to Database
        # session=Session()

        cmd = Command(command, len(command), timeinseconds, out_byte)
        session.add(cmd)
        session.commit()

        # session.query(Command).filter_by(name='ed').all()
