import logging
import os
from functools import wraps
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from flask import (Blueprint, abort, current_app, jsonify, redirect,
                   render_template, render_template_string, request, session,
                   url_for)

from report_app.main.report_database import ReportDatabase
from report_app.main.repository_report import RepositoryReport

main = Blueprint("main", __name__)

logger = logging.getLogger(__name__)

AUTHLIB_CLIENT = "authlib.integrations.flask_client"


@main.record
def setup_auth0(setup_state):
    """This is a Blueprint function that is called during app.register_blueprint(main)
    Use this function to set up Auth0

    Args:
        setup_state (Flask): The Flask app itself
    """
    logger.debug("setup_auth0()")
    app = setup_state.app
    OAuth(app)
    auth0 = app.extensions.get(AUTHLIB_CLIENT)
    auth0.register(
        "auth0",
        client_id=os.getenv("AUTH0_CLIENT_ID"),
        client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
        client_kwargs={
            "scope": "openid profile email",
        },
        server_metadata_url=f'https://{os.getenv("AUTH0_DOMAIN")}/'
        + ".well-known/openid-configuration",
    )


def requires_auth(function_f):
    """Redirects the web page to /index if user is not logged in

    Args:
        function_f: The calling function

    Returns:
        A redirect to /index or continue with the function that was called
    """

    @wraps(function_f)
    def decorated(*args, **kwargs):
        logger.debug("requires_auth()")
        if "user" not in session:
            return redirect("/index")
        return function_f(*args, **kwargs)

    return decorated


@main.route("/home")
@main.route("/start")
@requires_auth
def home():
    """Home page for the application

    Returns:
        Loads the templates/home.html page
    """
    logger.debug("home()")
    return render_template("home.html")


@main.route("/index")
@main.route("/")
def index():
    """Display the landing page for the application

    Returns:
        Loads the templates/index.html page
    """
    logger.debug("index()")
    return render_template(
        "index.html",
        session=session.get("user"),
    )


@main.route("/login")
def login():
    """When click on the login button connect to Auth0

    Returns:
        Creates a redirect to /callback if succesful
    """
    logger.debug("login()")
    auth0 = current_app.extensions.get(AUTHLIB_CLIENT)
    return auth0.auth0.authorize_redirect(
        redirect_uri=url_for("main.callback", _external=True)
    )


@main.route("/callback", methods=["GET", "POST"])
def callback():
    """If login succesful redirect to /home

    Returns:
        Redirects to /home if user has correct email domain else redirects to /logout
    """
    logger.debug("callback()")
    try:
        auth0 = current_app.extensions.get(AUTHLIB_CLIENT)
        token = auth0.auth0.authorize_access_token()
        session["user"] = token
    except (Exception,):  # pylint: disable=W0703
        return render_template("500.html"), 500

    user_email = session["user"]["userinfo"]["email"]

    if (
        "@digital.justice.gov.uk" in user_email
        or "@justice.gov.uk" in user_email
        or "@cica.gov.uk" in user_email
        or "@hmcts.net" in user_email
    ):
        logger.info("User has approved email domain")
        return redirect("/home")

    logger.warning("User does not have an approved email domain")
    return redirect("/logout")


@main.route("/logout")
def logout():
    """When click on the logout button, clear the session, and log out of Auth0

    Returns:
        Redirects to /index
    """
    logger.debug("logout()")
    session.clear()
    return redirect(
        "https://"
        + os.getenv("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("main.index", _external=True),
                "client_id": os.getenv("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


@main.errorhandler(404)
def page_not_found(err):
    # pylint: disable=unused-argument
    """Load 404.html when page not found error occurs

    Args:
        err : N/A

    Returns:
        Load the templates/404.html page
    """
    logger.debug("page_not_found()")
    return render_template("404.html"), 404


@main.errorhandler(403)
def server_forbidden(err):
    # pylint: disable=unused-argument
    """Load 403.html when server forbids error occurs

    Args:
        err : N/A

    Returns:
        Load the templates/403.html page
    """
    logger.debug("server_forbidden()")
    return render_template("403.html"), 403


@main.errorhandler(500)
def unknown_server_error(err):
    # pylint: disable=unused-argument
    """Load 500.html when unknown server error occurs

    Args:
        err : N/A

    Returns:
        Load the templates/500.html page
    """
    logger.debug("unknown_server_error()")
    return render_template("500.html"), 500


def __is_request_correct(the_request):
    """Check request is a POST and has the correct API key

    Args:
        the_request: the incoming data request object
    """
    correct = False
    if (
        the_request.method == "POST"
        and "X-API-KEY" in the_request.headers
        and the_request.headers.get("X-API-KEY") == os.getenv("API_KEY")
    ):
        logger.debug("is_request_correct(): api key correct")
        correct = True
    else:
        logger.warning("is_request_correct(): incorrect api key")
    return correct


@main.route("/api/v2/update-github-reports", methods=["POST"])
def update_github_reports():
    """Update all GitHub repository reports we hold

    This will overwrite any existing reports storing each report
    in the database as a new record.
    """
    if __is_request_correct(request) is False:
        abort(400)

    RepositoryReport(request.json).update_all_github_reports()

    return jsonify({"message": "GitHub reports updated"}), 200


@main.route("/api/v2/compliant-repository/<repository_name>", methods=["GET"])
# Deprecated API endpoints: These will be removed in a future release
@main.route("/api/v1/compliant_public_repositories/endpoint/<repository_name>", methods=["GET"])
@main.route("/api/v1/compliant_public_repositories/<repository_name>", methods=["GET"])
def display_badge_if_compliant(repository_name: str) -> dict:
    """Display a badge if a repository is considered compliant.
    Compliance is determined by the status field in the database.

    Private repositories are not supported and will return a 403 error.

    Args:
        repository_name: the name of the repository to check
    """
    dynamo_db = ReportDatabase(
        table_name=os.getenv("DYNAMODB_TABLE_NAME"),
        access_key=os.getenv("DYNAMODB_ACCESS_KEY_ID"),
        secret_key=os.getenv("DYNAMODB_SECRET_ACCESS_KEY"),
        region=os.getenv("DYNAMODB_REGION"),
    )

    try:
        repository = dynamo_db.get_repository_report(repository_name)
    except KeyError:
        abort(404)
    if repository['data']['is_private']:
        abort(403, "Private repositories are not supported, and %s is private" % repository_name)

    if repository["data"]["status"]:
        return {
            "schemaVersion": 1,
            "label": "MoJ Compliant",
            "message": "PASS",
            "color": "005ea5",
            "labelColor": "231f20",
            "style": "for-the-badge",
        }

    return {
        "schemaVersion": 1,
        "label": "MoJ Compliant",
        "message": "FAIL",
        "color": "d4351c",
        "style": "for-the-badge",
        "isError": "true",
    }


@main.route("/public-github-repositories.html")
def public_github_repositories():
    return render_template("public-github-repositories.html",
                           last_updated="today",
                           compliant=1,
                           non_compliant=2)


@main.route('/search')
def search():
    query = request.args.get('q')
    search_results = []

    compliant_repos = [
        {
            "name": "moj-analytical-services",
            "description": "The repository for the MoJ Analytical Services team",
            "url": ""
        },
    ]
    for repo in compliant_repos:
        if query.lower() in repo['name'].lower():
            search_results.append(repo)

    # Render the search results to a string and return it
    return render_template_string(
        """
        <ul class="govuk-list">
            {% for repo in search_results %}
                <p><a href="{{ repo.url }}">{{ repo.name }}</a></p>
            {% else %}
                <p>No results found</p>
            {% endfor %}
        </ul>
        """,
        search_results=search_results
    )