class Dynamodb
  attr_reader :db, :table

  # Max. number of items for the `batch_get_item` method of the DynamoDB client
  # https://docs.aws.amazon.com/sdk-for-ruby/v3/api/Aws/DynamoDB/Client.html#batch_get_item-instance_method
  # If we're using DynamoDB as our storage backend, we need to fetch items in chunks
  # no larger than this.
  MAX_ITEMS = 100

  def initialize(params = {})
    @db = params.fetch(:db, Aws::DynamoDB::Client.new(
      region: ENV.fetch("DYNAMODB_REGION"),
      access_key_id: ENV.fetch("DYNAMODB_ACCESS_KEY_ID"),
      secret_access_key: ENV.fetch("DYNAMODB_SECRET_ACCESS_KEY"),
    ))
    @table = params.fetch(:table, ENV.fetch("DYNAMODB_TABLE_NAME"))
  end

  def list_files
    db.scan(
      table_name: table,
      expression_attribute_names: { "#F" => "filename" },
      projection_expression: "#F",
    ).items.map { |i| i["filename"] }.sort
  end

  def store_file(file, content)
    db.put_item(table_name: table, item: { filename: file, content: content, stored_at: Time.now.to_s})
  end

  def retrieve_file(file)
    item = get_item(file)
    item.nil? ? nil : item["content"]
  end

  def retrieve_files(filenames)
    rtn = {}
    filenames.each_slice(MAX_ITEMS) do |chunk|
      hash = batch_get_item(chunk)
      rtn.merge!(hash)
    end
    rtn
  end

  def stored_at(file)
    exists?(file) ? Time.parse(get_item(file)["stored_at"]) : nil
  end

  def exists?(file)
    !retrieve_file(file).nil?
  end

  private

  def batch_get_item(keys)
    result = db.batch_get_item(
      request_items: {
        table => {
          keys: keys.map {|k| {"filename" => k}}
        }
      }
    )

    items = result.responses[table]

    items.inject({}) do |hash, item|
      filename = item.delete("filename")
      hash[filename] = item
      hash
    end

    # keys.inject({}) { |hash, key| hash[key] = retrieve_file(key); hash }
  end

  def get_item(key)
    db.get_item(
      key: { filename: key },
      table_name: table,
    ).item
  end
end
