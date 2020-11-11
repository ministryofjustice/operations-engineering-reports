class ItemList
  attr_reader :logger, :store

  DATA_KEY = "data"
  UPDATED_AT = "updated_at"

  def initialize(params)
    @json_file = params.fetch(:file)
    @logger = params.fetch(:logger)
    @store = params.fetch(:store, Filestore.new)
  end

  def list
    @list ||= data.nil? ? [] : data.fetch(DATA_KEY)
  end

  def updated_at
    @updated_at ||= data.nil? ? "" : string_to_formatted_time(data.fetch(UPDATED_AT))
  end

  private

  def data
    @data ||= read_data
  end

  def read_data
    data = nil

    unless store.exists?(@json_file)
      logger.info "No such file #{@json_file}"
    else
      begin
        json = store.retrieve_file @json_file
        data = json.nil? ? {} : JSON.parse(json)
      rescue JSON::ParserError
        logger.info "Malformed JSON file: #{@json_file}"
      end
    end

    data
  end

  def string_to_formatted_time(str)
    DateTime.parse(str).strftime("%Y-%m-%d %H:%M:%S")
  end
end
