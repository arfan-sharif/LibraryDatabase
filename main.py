#main.py
from website import create_app
#Run Application from Here
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
