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
  attr_reader :group_by

  REPOSITORY = "repository" # Github repository name
  LOGIN = "login" # Github login of collaborator

  def initialize(params)
    @group_by = params.fetch(:group_by, REPOSITORY)
    super(params)
  end

  def list
    @list ||=
      begin
        super.map { |i| RepoCollab.new(i) }
      end
  end

  private

end
