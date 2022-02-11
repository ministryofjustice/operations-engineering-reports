FROM ruby:latest

RUN addgroup -gid 1000 --system appgroup \
  && adduser -uid 1000 --system appuser \
  && adduser appuser appgroup \
  && gem install bundler \
  && bundle config

WORKDIR /app

COPY Gemfile Gemfile.lock ./
RUN bundle install

COPY app.rb ./
COPY views/ ./views
COPY lib/ ./lib
COPY public/ ./public
RUN mkdir /app/data

RUN chown -R appuser:appgroup /app

USER 1000

CMD ["ruby", "app.rb", "-o", "0.0.0.0"]
