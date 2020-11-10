require "spec_helper"

describe ItemList do
  let(:json) { data.to_json }
  let(:logger) { double(Sinatra::CommonLogger) }

  let(:params) { {
    file: "foo.json",
    key: key,
    logger: logger,
  } }

  let(:key) { "mylist" }
  let(:mylist) { ["foo", "bar", "baz"] }
  let(:updated_at) { "2020-07-14 12:34:56" }
  let(:data) {
    {
      mylist: mylist,
      updated_at: updated_at,
    }
  }

  subject(:item_list) { described_class.new(params) }

  before do
    allow(FileTest).to receive(:exists?).and_return(true)
    allow(File).to receive(:read).and_return(json)
    allow(logger).to receive(:info)
  end

  context "when there is valid json data" do
    it "has updated_at" do
      expect(item_list.updated_at).to eq(updated_at)
    end

    it "returns mylist" do
      expect(item_list.list).to eq(mylist)
    end

    it "has some todos" do
      expect(item_list.todo_count).to eq(3)
    end
  end

  context "when there is no json data file" do
    before do
      allow(FileTest).to receive(:exists?).and_return(false)
    end

    it "returns an empty list" do
      expect(item_list.list).to eq([])
    end

    it "has empty updated_at" do
      expect(item_list.updated_at).to eq("")
    end

    it "has zero todos" do
      expect(item_list.todo_count).to eq(0)
    end
  end

  context "when there is invalid json data in the file" do
    let(:json) { "This is not valid JSON" }

    it "returns an empty list" do
      expect(item_list.list).to eq([])
    end

    it "has empty updated_at" do
      expect(item_list.updated_at).to eq("")
    end

    it "has zero todos" do
      expect(item_list.todo_count).to eq(0)
    end
  end
end
