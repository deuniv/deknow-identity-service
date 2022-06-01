from deuniv.app import create_app

if __name__ == '__main__':
    create_app = create_app()
    create_app.run()
else:
    my_app = create_app()