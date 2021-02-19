#!/usr/bin/env ruby

require "bundler/setup"
require "json"
require "sinatra"
require "./lib/opseng_reports"

CONTENT_TYPE_JSON = "application/json"

# Different list item classes to use for different reports
LIST_RENDERER = {
  "github_collaborators" => Collaborators,
  "github_repositories" => GithubRepositories
}

if development?
  require "sinatra/reloader"
  require "pry-byebug"
end

def update_json_data(store, docpath, request)
  require_api_key(request) do
    file = datafile(docpath)
      store.store_file(file, request.body.read)
  end
end

def require_api_key(request)
  if correct_api_key?(request)
    yield
    status 200
  else
    status 403
  end
end

def correct_api_key?(request)
  expected_key = ENV.fetch("API_KEY")
  provided_key = request.env.fetch("HTTP_X_API_KEY", "dontsetthisvalueastheapikey")
  expected_key == provided_key
end

def datafile(docpath)
  "data/#{docpath}.json"
end

def get_data_from_json_file(docpath, klass)
  klass.new(
    store: store,
    file: datafile(docpath),
    logger: logger,
  )
end

def serve_json_data(docpath)
  store.retrieve_file(datafile(docpath))
end

def render_item_list(docpath, klass = ItemList)
  template = docpath.to_sym

  item_list = get_data_from_json_file(docpath, klass)

  locals = {
    updated_at: item_list.updated_at,
    data: item_list,
  }

  erb template, locals: locals
end

def accept_json?(request)
  accept = request.env["HTTP_ACCEPT"]
  accept == CONTENT_TYPE_JSON
end

def store
  ENV.has_key?("DYNAMODB_TABLE_NAME") ? Dynamodb.new : Filestore.new
end

############################################################

get "/" do
  erb :index
end

get "/:docpath" do
  docpath = params.fetch("docpath")
  if accept_json?(request)
     serve_json_data(docpath)
  else
    render_item_list(docpath, LIST_RENDERER.fetch(docpath, ItemList))
  end
end

post "/:docpath" do
  update_json_data(store, params.fetch("docpath"), request)
end
