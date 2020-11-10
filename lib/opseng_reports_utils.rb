module OpsengReportsUtils
  def decimals(value, decimals = 2)
    sprintf("%0.#{decimals}f", value)
  end

  def commify(value)
    whole, decimal = decimals(value).split(".")
    with_commas = whole.gsub(/\B(?=(...)*\b)/, ",")
    [with_commas, decimal].join(".")
  end

  def link_to(text, href)
    "<a href='#{href}'>#{text}</a>"
  end
end

helpers OpsengReportsUtils
