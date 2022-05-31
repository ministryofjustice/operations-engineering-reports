class RepoCollab
  attr_reader :repository, :login, :repo_url, :login_url, :issues, :href, :permission, :last_commit

  def initialize(hash)
    @repository = hash.fetch("repository")
    @repo_url = hash.fetch("repo_url")
    @login = hash.fetch("login")
    @login_url = hash.fetch("login_url")
    @issues = hash.fetch("issues")
    @href = hash.fetch("href")
    @permission = hash.fetch("permission")  
    @last_commit = hash.fetch("last_commit", "")
  end
end

class Collaborators < ItemList
  REPOSITORY = :repository # Github repository name
  LOGIN = :login # Github login of collaborator

  def list
    @list ||= super.map { |i| RepoCollab.new(i) }
  end

  def repositories
    list
      .each_with_object({}) { |i, hash| hash[i.repository] = i; }
      .values
      .sort_by(&:repository)
  end

  def collaborators
    list
      .each_with_object({}) { |i, hash| hash[i.login] = i; }
      .values
      .sort_by(&:login)
  end

  def repository_collaborators(repo_name)
    list
      .filter { |i| i.repository == repo_name }
      .sort_by { |i| i.login }
  end

  def collaborator_repositories(login)
    list
      .filter { |i| i.login == login }
      .sort_by { |i| i.repository }
  end
end
