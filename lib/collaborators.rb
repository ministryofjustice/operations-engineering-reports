class RepoCollab
  attr_reader :repository, :login, :repo_url, :login_url

  def initialize(hash)
    @repository = hash.fetch("repository")
    @repo_url = hash.fetch("repo_url")
    @login = hash.fetch("login")
    @login_url = hash.fetch("login_url")
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
      .inject({}) { |hash, i| hash[i.repository] = i; hash }
      .values
      .sort { |a,b| a.repository <=> b.repository }
  end

  def collaborators
    list.map(&:login).sort.uniq
  end

  def repository_collaborators(repo_name)
    list.filter { |i| i.repository == repo_name }
  end

  def collaborator_repositories(login)
    list.filter { |i| i.login == login }
  end
end
