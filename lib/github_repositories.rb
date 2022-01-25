class GithubRepository
  attr_reader :name, :default_branch, :report, :status, :url, :last_push, :issues_enabled

  FAIL = "FAIL"

  def initialize(hash)
    @name = hash.fetch("name")
    @default_branch = hash.fetch("default_branch")
    @status = hash.fetch("status")
    @url = hash.fetch("url")
    @last_push = hash.fetch("last_push")
    @report = hash.fetch("report")
    @issues_enabled = hash.fetch("issues_enabled")
  end

  def readable_problem(str)
    {
      "default_branch_main" => "The default branch is not `main`",
      "has_default_branch_protection" => "Branch protection is not enabled for `#{default_branch}`",
      "requires_approving_reviews" => "Pull request reviews are not required",
      "administrators_require_review" => "Administrator PRs do not require reviews",
      "issues_section_enabled" => "The issues section is not enabled"
    }.fetch(str) { str }
  end

  def default_branch_main?
    report["default_branch_main"]
  end

  def fail?
    status == FAIL
  end
end

class GithubRepositories < ItemList
  def list
    @list ||= super
      .map { |i| GithubRepository.new(i) }
      .sort_by(&:name)
  end

  def failing
    list.filter(&:fail?)
  end
end

__END__
      "organization": "ministryofjustice",
      "name": "cloud-platform-concourse",
      "default_branch": "main",
      "url": "https://github.com/ministryofjustice/cloud-platform-concourse",
      "status": "PASS",
      "report": {
        "default_branch_main": true,
        "has_main_branch_protection": true,
        "requires_approving_reviews": true,
        "requires_code_owner_reviews": true,
        "administrators_require_review": true,
        "dismisses_stale_reviews": true,
        "team_is_admin": true,
        "issues_enabled": true
