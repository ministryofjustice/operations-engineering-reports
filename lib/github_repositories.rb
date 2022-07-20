class GithubRepository
  attr_reader :name, :default_branch, :report, :status, :url, :last_push, :issues_enabled

  FAIL = "FAIL"
  PASS = "PASS"

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
      "administrators_require_review" => "Administrator pull requests do not require reviews",
      "issues_section_enabled" => "The issues section is not enabled",
      "requires_code_owner_reviews" => "Pull request code owner reviews are not required",
      "has_require_approvals_enabled" => "Pull request review approvals are not required"
    }.fetch(str) { str }
  end

  def default_branch_main?
    report["default_branch_main"]
  end

  def fail?
    status == FAIL
  end

  def pass?
    status == PASS
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

  def pass
    list.filter(&:pass?)
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
        "has_default_branch_protection": true,
        "requires_approving_reviews": true,
        "administrators_require_review": true,
        "issues_section_enabled": true
        "requires_code_owner_reviews": true,
        "has_require_approvals_enabled": true
      }
