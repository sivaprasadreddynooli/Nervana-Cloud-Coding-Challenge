"""
Details the various flask endpoints for processing and retrieving
command details as well as a swagger spec endpoint
"""
from multiprocessing import Process, Queue
import sys
from flask import Flask, request, jsonify
from flask_swagger import swagger
from db import session, engine
from base import Base, Command
from command_parser import get_valid_commands, process_command_output

app = Flask(__name__)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


@app.route('/commands', methods=['GET'])
def get_command_output():
    """
    Returns as json the command details that have been processed
    ---
    tags: [commands]
    responses:
      200:
        description: Commands returned OK
      400:
        description: Commands not found
    """

    commands = session.query(Command)

    jlist = []

    for cmd in commands:
        dict = {}
        dict['id'] = cmd.id
        dict['command_string'] = cmd.command_string
        dict['length'] = cmd.length
        dict['duration'] = cmd.duration
        if cmd.output:
            dict['output'] = cmd.output.decode('us-ascii').rstrip('\n')
        else:
            dict['output'] = ''
        jlist.append(dict)
        # commands=[commmand.serialize for command in commands]
    # TODO: format the query result

    return jsonify(jlist)


@app.route('/commands', methods=['POST'])
def process_commands():
    """
    Processes commmands from a command list
    ---
    tags: [commands]
    parameters:
      - name: filename
        in: formData
        description: filename of the commands text file to parse
                     which exists on the server
        required: true
        type: string
    responses:
      200:
        description: Processing OK
    """

    fi = request.args.get('filename')
    file_data = request.args.get('file_data')

    if file_data:
        queue = Queue()
        get_valid_commands(queue, fi, file_data=file_data)
    else:

        queue = Queue()
        get_valid_commands(queue, fi)

    processes = [Process(target=process_command_output, args=(queue, ))
                 for num in range(2)]
    for process in processes:
        process.start()
    for process in processes:
        process.join()  # temporary drop

    return 'Successfully processed commands.'


@app.route('/database', methods=['POST'])
def make_db():
    """
    Creates database schema
    ---
    tags: [db]
    responses:
      200:
        description: DB Creation OK
    """

    Base.metadata.create_all(engine)
    return 'Database creation successful.'


@app.route('/database', methods=['DELETE'])
def drop_db():
    """
    Drops all db tables
    ---
    tags: [db]
    responses:
      200:
        description: DB table drop OK
    """

    Base.metadata.drop_all(engine)
    return 'Database deletion successful.'

if __name__ == '__main__':
    port = 8080
    use_reloader = True
    make_db()  # temporary database invoke

    # provides some configurable options

    for arg in sys.argv[1:]:
        if '--port' in arg:
            port = int(arg.split('=')[1])
        elif '--use_reloader' in arg:
            use_reloader = arg.split('=')[1] == 'true'

    app.run(port=port, debug=True, use_reloader=use_reloader)


@app.route('/spec')
def swagger_spec():
    """
    Display the swagger formatted JSON API specification.
    ---
    tags: [docs]
    responses:
      200:
        description: OK status
    """
    spec = swagger(app)
    spec['info']['title'] = "Nervana cloud challenge API"
    spec['info']['description'] = ("Nervana's cloud challenge " +
                                   "for interns and full-time hires")
    spec['info']['license'] = {
        "name": "Nervana Proprietary License",
        "url": "http://www.nervanasys.com",
    }
    spec['info']['contact'] = {
        "name": "Nervana Systems",
        "url": "http://www.nervanasys.com",
        "email": "info@nervanasys.com",
    }
    spec['schemes'] = ['http']
    spec['tags'] = [
        {"name": "db", "description": "database actions (create, delete)"},
        {"name": "commands", "description": "process and retrieve commands"}
    ]
    return jsonify(spec)
