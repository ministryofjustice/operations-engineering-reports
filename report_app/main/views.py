""" Routes and OAuth code """
import logging
import os
from functools import wraps
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from flask import (
    Blueprint,
    redirect,
    render_template,
    session,
    url_for,
    request,
    current_app,
)
from report_app.main.repositories import Repositories

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
    else:
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


@main.route("/public-github-repositories.html")
def public_repos_page():
    """The public repository report page

    Returns:
        Loads the templates/public-github-repositories.html page
    """
    logger.debug("public_repos_page()")
    repository = Repositories("public")
    if repository.is_database_ready():
        compliant_repos = repository.get_compliant_repositories()
        non_compliant_repos = repository.get_non_compliant_repositories()
        return render_template(
            "public-github-repositories.html",
            updated_at=repository.get_stored_at_date(),
            total_repos=repository.get_total_repositories(),
            number_compliant_repos=len(compliant_repos),
            number_non_compliant_repos=len(non_compliant_repos),
            compliant_repos=compliant_repos,
            non_compliant_repos=non_compliant_repos,
            session=session.get("user"),
        )
    return render_template(
        "public-github-repositories.html", session=session.get("user")
    )


@main.route("/private-github-repositories.html")
@requires_auth
def private_repos_page():
    """The private repo report page

    Returns:
        Loads the templates/private-github-repositories.html page
    """
    logger.debug("private_repos_page()")
    repository = Repositories("private")
    if repository.is_database_ready():
        compliant_repos = repository.get_compliant_repositories()
        non_compliant_repos = repository.get_non_compliant_repositories()
        return render_template(
            "private-github-repositories.html",
            updated_at=repository.get_stored_at_date(),
            total_repos=repository.get_total_repositories(),
            number_compliant_repos=len(compliant_repos),
            number_non_compliant_repos=len(non_compliant_repos),
            compliant_repos=compliant_repos,
            non_compliant_repos=non_compliant_repos,
            session=session.get("user"),
        )
    return render_template(
        "private-github-repositories.html", session=session.get("user")
    )


def is_request_correct(the_request):
    """Check request is a POST and has the correct API key

    Args:
        new_request (the_request): the incoming data request object
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


def apply_public_data(new_request):
    """Add public data item to the table

    Args:
        new_request (request): the incoming data request object
    """
    logger.debug("apply_public_data()")

    if is_request_correct(new_request):
        repository = Repositories("public")
        repository.update_data(new_request.json)


def apply_private_data(new_request):
    """Add private data item to the table

    Args:
        new_request (request): the incoming data request object
    """
    logger.debug("apply_private_data()")

    if is_request_correct(new_request):
        repository = Repositories("private")
        repository.update_data(new_request.json)


@main.route("/update_private_repositories", methods=["POST"])
def update_private_repositories():
    """Receive data to either add or update the private repo report item in the table
       within the database

    Returns:
        N/A: N/A
    """
    logger.debug("update_private_repositories()")
    apply_private_data(request)
    return ""


@main.route("/update_public_repositories", methods=["POST"])
def update_public_repositories():
    """Receive data to either add or update the public repo report item in the table
       within the database

    Returns:
        N/A: N/A
    """
    logger.debug("update_public_repositories()")
    apply_public_data(request)
    return ""


@main.route('/api/v1/compliant_public_repositories/<repository_name>', methods=['GET'])
def compliant_repository(repository_name):
    """Find a repository in compliant repositories list

    Args:
        repository_name (string): name of repository to find

    Returns:
        dict: json result true if find repository in compliant repositories list
    """
    logger.debug("compliant_repository()")
    repository = Repositories("public")
    if repository.is_database_ready():
        compliant_repos = repository.get_compliant_repositories()
        for compliant_repo in compliant_repos:
            if compliant_repo.get("name") == repository_name:
                return {"result": "PASS"}
    return {"result": "FAIL"}


@main.route('/api/v1/compliant_public_repositories/endpoint/<repository_name>', methods=['GET'])
def compliant_repository_endpoint(repository_name):
    """Find a repository in compliant repositories list

    Args:
        repository_name (string): name of repository to find

    Returns:
        dict: json result true if find repository in compliant repositories list
    """
    logger.debug("compliant_repository_endpoint()")
    repository = Repositories("public")
    if repository.is_database_ready():
        compliant_repos = repository.get_compliant_repositories()
        for compliant_repo in compliant_repos:
            if compliant_repo.get("name") == repository_name:
                return {"schemaVersion": 1, "label": "MoJ Compliant", "message": "PASS", "color": "005ea5"}
    return {"schemaVersion": 1, "label": "MoJ Compliant", "message": "FAIL", "color": "d4351c", "isError": "true"}
