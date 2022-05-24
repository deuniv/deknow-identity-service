import os
import json
from flask import Flask, g, redirect, request, url_for
from urllib.parse import urlencode, unquote
from deuniv.db import get_db
from deuniv.service import parseUrlAndFetch

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY = "dev",
        DATABASE=os.path.join(app.instance_path, "deuniv.db")
    )

    @app.route("/", methods=["GET", "POST"])
    def hello_world():
        if request.method == 'POST':
            url =  request.form.get('url')
            return redirect(url_for('.get_details_from_url', url=url), code=307)
        else:
            return """
                <form method="POST">
                    <div>
                        <h1>Header</h1></div>
                    <div>
                        <label for="url" class="formbuilder-text-label">URL</label>
                        <br>
                        <input style="width: 80%;" type="text" class="form-control" name="url" placeholder="Enter URL here">
                    </div>
                    <div>
                        <button type="submit" class="btn-default btn">Submit</button>
                    </div>
                </form>
                """
    
    @app.route("/details", methods=["POST"])
    def get_details_from_url():
        db = get_db()
        url = request.args.get("url", default=None)
        if url:
            url = unquote(url)
        return parseUrlAndFetch(db, url)
    
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    app.logger.info("Initiating db...")
    db.init_app(app)

    return app