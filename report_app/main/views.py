import datetime
import logging
import os
from collections import Counter
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
@main.route("/index")
@main.route("/")
def index():
    '''Entrypoint into the application'''
    all_reports = ReportDatabase(
        os.getenv("DYNAMODB_TABLE_NAME")
    ).get_all_repository_reports()

    compliant_reports = [report for report in all_reports if report['data']['status']]
    non_compliant_reports = [report for report in all_reports if not report['data']['status']]

    all_infractions = [infraction for report in non_compliant_reports for infraction in report['data']['infractions']]
    human_readable_infractions = []
    for infraction in all_infractions:
        match infraction:
            case "administrators_require_review equalling False is not compliant":
                human_readable_infractions.append("Administrators require review")
            case "default_branch_main equalling False is not compliant":
                human_readable_infractions.append("Default branch is not main")
            case "has_default_branch_protection equalling False is not compliant":
                human_readable_infractions.append("Default branch is not protected")
            case "has_description equalling False is not compliant":
                human_readable_infractions.append("Repository has no description")
            case "has_license equalling False is not compliant":
                human_readable_infractions.append("Repository has no license")
            case "has_require_approvals_enabled equalling False is not compliant":
                human_readable_infractions.append("Require approvals is not enabled")
            case "issues_section_enabled equalling False is not compliant":
                human_readable_infractions.append("Issues section is not enabled")
            case "requires_approving_reviews equalling False is not compliant":
                human_readable_infractions.append("Requires approving reviews is not enabled")
            case _:
                human_readable_infractions.append("Unknown infraction")
    common_infractions = Counter(human_readable_infractions).most_common(3)

    return render_template("home.html",
                           total=len(all_reports),
                           compliant=len(compliant_reports),
                           last_updated=all_reports[0]["stored_at"],
                           common_infractions=common_infractions,
                           non_compliant=len(non_compliant_reports))


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
    """If login succesful redirect to /index

    Returns:
        Redirects to /home if user has correct email domain else redirects to /logout
    """
    try:
        auth0 = current_app.extensions.get(AUTHLIB_CLIENT)
        token = auth0.auth0.authorize_access_token()
        session["user"] = token
    except (KeyError, AttributeError):
        return render_template("500.html"), 500

    try:
        user_email = session["user"]["userinfo"]["email"]
    except KeyError:
        logger.warning("Unauthed User does not have an email address")
        return render_template("500.html"), 500
    if user_email is None:
        logger.warning("User %s does not have an email address", user_email)
        return redirect("/logout")

    if __is_allowed_email(user_email):
        logger.info("User %s has approved email domain", user_email)
        return redirect("/home")

    logger.warning("User %s does not have an approved email domain", user_email)
    return redirect("/logout")


def __is_allowed_email(email_address):
    allowed_domains = (
        "@digital.justice.gov.uk",
        "@justice.gov.uk",
        "@cica.gov.uk",
        "@hmcts.net",
    )
    return any(email_address.endswith(domain) for domain in allowed_domains)


@main.route("/logout", methods=["GET", "POST"])
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
    """Load 404.html when page not found error occurs

    Args:
        err : N/A

    Returns:
        Load the templates/404.html page
    """
    logger.debug("A request was made to a page that doesn't exist %s", err)
    return render_template("404.html"), 404


@main.errorhandler(403)
def server_forbidden(err):
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
    """Load 500.html when unknown server error occurs

    Args:
        err : N/A

    Returns:
        Load the templates/500.html page
    """
    logger.error("An unknown server error occurred: %s", err)
    return render_template("500.html"), 500


@main.errorhandler(504)
def gateway_timeout(err):
    """Load 504.html when gateway timeout error occurs

    Args:
        err : N/A

    Returns:
        Load the templates/504.html page
    """
    logger.error("A gateway timeout error occurred: %s", err)
    return render_template("504.html"), 504


def _is_request_correct(the_request):
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
    logger.info("update_github_reports(): received request from %s", request.remote_addr)
    if _is_request_correct(request) is False:
        logger.error("update_github_reports(): incorrect api key, from %s", request.remote_addr)
        abort(400)

    logging.info("update_github_reports(): updating all GitHub reports")
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
        os.getenv("DYNAMODB_TABLE_NAME")
    )

    try:
        repository = dynamo_db.get_repository_report(repository_name)
    except KeyError:
        abort(404)
    if repository['data']['is_private']:
        abort(403, "Private repositories are not supported")

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


@main.route("/public-github-repositories.html", methods=["GET"])
def public_github_repositories():
    public_repositories = ReportDatabase(
        os.getenv("DYNAMODB_TABLE_NAME")
    ).get_all_public_repositories()

    compliant_repos = [repo for repo in public_repositories if repo['data']['status']]
    non_compliant_repos = [repo for repo in public_repositories if not repo['data']['status']]

    return render_template("public-github-repositories.html",
                           last_updated=public_repositories[0]["stored_at"],
                           total=len(public_repositories),
                           compliant=len(compliant_repos),
                           non_compliant=len(non_compliant_repos))


@main.route("/private-github-repositories.html")
@requires_auth
def private_github_repositories():
    private_repositories = ReportDatabase(
        os.getenv("DYNAMODB_TABLE_NAME")
    ).get_all_private_repositories()

    compliant_repos = [repo for repo in private_repositories if repo['data']['status']]
    non_compliant_repos = [repo for repo in private_repositories if not repo['data']['status']]

    return render_template("private-github-repositories.html",
                           last_updated=private_repositories[0]["stored_at"],
                           total=len(private_repositories),
                           compliant=len(compliant_repos),
                           non_compliant=len(non_compliant_repos))


@main.route('/search-public-repositories', methods=['GET'])
def search_public_repositories():
    query = request.args.get('q')
    search_results = []

    public_reports = ReportDatabase(
        os.getenv("DYNAMODB_TABLE_NAME")
    ).get_all_public_repositories()

    for repo in public_reports:
        if query.lower() in repo['name'].lower():
            search_results.append(repo)

    # Render the search results to a string and return it
    return render_template_string(
        """
        <p class="govuk-heading-s">{{ search_results|length }} results found</p>
        <ul class="govuk-list">
            {% for repo in search_results %}
                <p><a href="/public-report/{{ repo.name }}">{{ repo.name }}</a></p>
            {% else %}
                <p>No results found</p>
            {% endfor %}
        </ul>
        """,
        search_results=search_results
    )


@main.route("/public-report/<repository_name>", methods=["GET"])
def display_individual_public_report(repository_name: str):
    """View the GitHub standards report for a repository"""
    try:
        report = ReportDatabase(
            os.getenv("DYNAMODB_TABLE_NAME")
        ).get_repository_report(repository_name)
    except KeyError:
        logger.warning("display_individual_public_report(): repository not found")
        abort(404)
    return render_template("/public-report.html", report=report)


@main.route("/compliant-public-repositories.html", methods=["GET"])
def display_compliant_public_repositories():
    """View all repositories that adhere to the MoJ GitHub standards"""
    compliant_repositories = ReportDatabase(
        os.getenv("DYNAMODB_TABLE_NAME")
    ).get_all_compliant_repository_reports()

    public_compliant_repositories = [repo for repo in compliant_repositories if not repo['data']['is_private']]

    return render_template("/compliant-public-repositories.html", compliant_repos=public_compliant_repositories)


@main.route("/non-compliant-public-repositories.html", methods=["GET"])
def display_noncompliant_public_repositories():
    """View all repositories that do not adhere to the MoJ GitHub standards"""
    non_compliant = ReportDatabase(
        os.getenv("DYNAMODB_TABLE_NAME")
    ).get_all_non_compliant_repository_reports()

    non_compliant_repositories = [repo for repo in non_compliant if not repo['data']['is_private']]

    return render_template("/non-compliant-public-repositories.html", non_compliant_repos=non_compliant_repositories)


@main.route("/all-public-repositories.html", methods=["GET"])
def display_all_public_repositories():
    """View all repositories that do not adhere to the MoJ GitHub standards"""
    all_reports = ReportDatabase(
        os.getenv("DYNAMODB_TABLE_NAME")
    ).get_all_repository_reports()

    public_reports = [repo for repo in all_reports if not repo['data']['is_private']]

    return render_template("/all-public-repositories.html", public_reports=public_reports)


@main.route('/search-private-repositories', methods=['GET'])
@requires_auth
def search_private_repositories():
    query = request.args.get('q')
    search_results = []

    private_repos = ReportDatabase(
        os.getenv("DYNAMODB_TABLE_NAME")
    ).get_all_private_repositories()

    for repo in private_repos:
        if query.lower() in repo['name'].lower():
            search_results.append(repo)

    # Render the search results to a string and return it
    return render_template_string(
        """
        <p class="govuk-heading-s">{{ search_results|length }} results found</p>
        <ul class="govuk-list">
            {% for repo in search_results %}
                <p><a href="/private-report/{{ repo.name }}">{{ repo.name }}</a></p>
            {% else %}
                <p>No results found</p>
            {% endfor %}
        </ul>
        """,
        search_results=search_results
    )


@main.route("/private-report/<repository_name>", methods=["GET"])
@requires_auth
def display_individual_private_report(repository_name: str):
    """View the GitHub standards report for a private repository"""
    try:
        report = ReportDatabase(
            os.getenv("DYNAMODB_TABLE_NAME")
        ).get_repository_report(repository_name)
    except KeyError:
        logger.warning("display_individual_private_report(): repository not found")
        abort(404)
    return render_template("/private-report.html", report=report)


@main.route("/compliant-private-repositories.html", methods=["GET"])
@requires_auth
def display_compliant_private_repositories():
    """View all private repositories that adhere to the MoJ GitHub standards"""
    compliant_repositories = ReportDatabase(
        os.getenv("DYNAMODB_TABLE_NAME")
    ).get_all_compliant_repository_reports()

    private_compliant_repositories = [repo for repo in compliant_repositories if repo['data']['is_private']]

    return render_template("/compliant-private-repositories.html", compliant_repos=private_compliant_repositories)


@main.route("/non-compliant-private-repositories.html", methods=["GET"])
@requires_auth
def display_noncompliant_private_repositories():
    """View all repositories that do not adhere to the MoJ GitHub standards"""
    non_compliant = ReportDatabase(
        os.getenv("DYNAMODB_TABLE_NAME")
    ).get_all_non_compliant_repository_reports()

    non_compliant_repositories = [repo for repo in non_compliant if repo['data']['is_private']]

    return render_template("/non-compliant-private-repositories.html", non_compliant_repos=non_compliant_repositories)


@main.route("/all-private-repositories.html", methods=["GET"])
@requires_auth
def display_all_private_repositories():
    """View all repositories that do not adhere to the MoJ GitHub standards"""
    all_reports = ReportDatabase(
        os.getenv("DYNAMODB_TABLE_NAME")
    ).get_all_repository_reports()

    private_reports = [repo for repo in all_reports if repo['data']['is_private']]

    return render_template("/all-private-repositories.html", private_reports=private_reports)


@main.route('/search-results-public', methods=['GET'])
def search_public_repositories_and_display_results():
    """Similar to search_public_repositories() but returns a results page instead of a string"""
    template = "public-results.html"
    query = request.args.get('q')
    search_results = []
    public_repos = ReportDatabase(
        os.getenv("DYNAMODB_TABLE_NAME")
    ).get_all_public_repositories()

    if query is None:
        return render_template(template, results=search_results)

    for repo in public_repos:
        if query.lower() in repo['name'].lower():
            search_results.append(repo)

    return render_template(template, results=search_results)


@main.route('/search-results-private', methods=['GET'])
@requires_auth
def search_private_repositories_and_display_results():
    """Similar to search_private_repositories() but returns a results page instead of a string"""
    template = "private-results.html"
    query = request.args.get('q')
    search_results = []
    private_repos = ReportDatabase(
        os.getenv("DYNAMODB_TABLE_NAME")
    ).get_all_private_repositories()

    if query is None:
        return render_template(template, results=search_results)

    for repo in private_repos:
        if query.lower() in repo['name'].lower():
            search_results.append(repo)

    return render_template(template, results=search_results)
