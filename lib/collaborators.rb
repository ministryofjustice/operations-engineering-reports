class RepoCollab
  attr_reader :repository, :login

  def initialize(hash)
    @repository = hash.fetch("repository")
    @login = hash.fetch("login")
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
