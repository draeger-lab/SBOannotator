from flask import Flask, render_template, request
import subprocess

# create a Flask object
app = Flask(__name__, template_folder='templates')


# defines a route. A route is a web page, or endpoint, and the @app.route decorator defines the URL,
# # in this case it is the root URL (i.e. /).

@app.route('/')
def index():
    # message = "Hello from Flask"
    return render_template("index.html")  # , messages=message)


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file uploaded'

    file = request.files['file']

    if file.filename == '':
        return 'No selected file'

    # Save the uploaded file to a specific location
    file.save('uploads/' + file.filename)

    # Call the background Python script using subprocess module
    process = subprocess.Popen(['python', 'main_app.py', file.filename]) # set python script to call
    output, errors = process.communicate()

    if errors:
        return f"Error occurred: {errors.decode('utf-8')}"

    return 'File uploaded and SBOannotator is running'


if __name__ == '__main__':
    app.run(debug=True)
