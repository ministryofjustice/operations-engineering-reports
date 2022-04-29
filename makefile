dev-server:
	API_KEY=soopersekrit ./app.rb -o 0.0.0.0

docker-dev-server:
	docker run --rm \
		-v $$(pwd)/data:/app/data \
		-e API_KEY=soopersekrit \
		-e RACK_ENV=production \
		-p 4567:4567 \
		foo

test:
	rspec

start-development-server:
	docker build -t foo .
	mkdir data || true
	echo '{"updated_at":"2020-11-10 16:46:15 +0000","data":[]}' > data/github_collaborators.json
	make docker-dev-server
	# Now visit http://localhost:4567/github_collaborators
